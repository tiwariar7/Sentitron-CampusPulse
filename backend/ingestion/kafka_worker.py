import asyncio
import json
import logging
import sys
import os
import time

# Ensure backend and ai-engine modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiokafka import AIOKafkaConsumer

try:
    from services.qdrant_service import qdrant_service
except ImportError:
    from backend.services.qdrant_service import qdrant_service

try:
    from ws_manager.manager import manager, SYSTEM_METRICS
except ImportError:
    from backend.ws_manager.manager import manager, SYSTEM_METRICS

# AI Imports
try:
    from ai_engine.classification.classifier import classifier_pipeline
    from ai_engine.embeddings.embedder import embedder
except ImportError as e:
    logging.error(f"Failed to load AI pipelines: {e}")
    # Mock fallback for pure backend testing without heavy models
    class MockClassifier:
        def classify(self, text): return "Other"
    class MockEmbedder:
        def embed(self, text): return [0.0] * 384
    classifier_pipeline = MockClassifier()
    embedder = MockEmbedder()

from services.db import AsyncSessionLocal, Complaint, Setting
from api.routers.notifications import trigger_notification
from sqlalchemy.future import select

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC = "complaints"
RETRY_TOPIC = "complaints-retry"
DLQ_TOPIC = "complaints-dlq"

async def process_raw_message(payload: dict):
    """Processes a single raw complaint payload and writes it to DB + Qdrant"""
    complaint_id_str = payload.get("complaint_id")
    text = payload.get("complaint_text", "")
    
    if not text:
        return None
        
    logger.info(f"Worker processing complaint: {complaint_id_str}")
    
    # 1. AI Classification & Embedding Latency calculation
    start_time = time.perf_counter()
    category = classifier_pipeline.classify(text)
    vector = embedder.embed(text)
    latency_ms = (time.perf_counter() - start_time) * 1000.0
    SYSTEM_METRICS["last_inference_latency_ms"] = latency_ms
    
    # 2. Vector Search (Clustering)
    similar_complaints = qdrant_service.find_similar(vector, limit=5, score_threshold=0.85)
    
    # Try to assign cluster ID
    assigned_cluster_id = payload.get("duplicate_group_id") or ""
    if not assigned_cluster_id:
        if similar_complaints:
            # Find first similar complaint in DB that has a duplicate_group_id
            for hit in similar_complaints:
                hit_complaint_id = hit.payload.get("complaint_id")
                async with AsyncSessionLocal() as session:
                    res = await session.execute(
                        select(Complaint).where(Complaint.complaint_id == hit_complaint_id)
                    )
                    hit_complaint = res.scalars().first()
                    if hit_complaint and hit_complaint.duplicate_group_id:
                        assigned_cluster_id = hit_complaint.duplicate_group_id
                        break
            
            # If none has one, create one based on the first similar hit
            if not assigned_cluster_id:
                first_hit_id = similar_complaints[0].payload.get("complaint_id")
                assigned_cluster_id = f"CLUSTER_{first_hit_id}"
        else:
            # Fallback seed group
            assigned_cluster_id = f"CLUSTER_{complaint_id_str}"
            
    # 3. Create database instance
    db_complaint = Complaint(
        complaint_id=complaint_id_str,
        source=payload.get("source"),
        department=payload.get("department"),
        category=category,
        subcategory=payload.get("subcategory"),
        complaint_text=text,
        sentiment_score=payload.get("sentiment_score"),
        urgency_level=payload.get("urgency_level"),
        escalation_flag=payload.get("escalation_flag"),
        resolved=payload.get("resolved"),
        duplicate_group_id=assigned_cluster_id,
        toxicity_score=payload.get("toxicity_score"),
        anonymous=payload.get("anonymous"),
        response_delay_hours=payload.get("response_delay_hours")
    )
    
    # 4. Atomic Write to Database
    async with AsyncSessionLocal() as session:
        session.add(db_complaint)
        await session.commit()
        await session.refresh(db_complaint)
        
        # 5. Toxicity & Escalation checking within processing transaction
        tox_limit = 70.0
        try:
            res = await session.execute(select(Setting).where(Setting.key == "toxicity_threshold"))
            tox_setting = res.scalars().first()
            if tox_setting and tox_setting.value:
                tox_limit = float(json.loads(tox_setting.value))
        except Exception as e:
            logger.warning(f"Failed to read toxicity setting: {e}")
            
        if db_complaint.toxicity_score > tox_limit:
            await trigger_notification(
                db=session,
                title="Toxicity Spike Detected",
                message=f"Incident {db_complaint.complaint_id} triggered a toxicity warning (Score: {db_complaint.toxicity_score}).",
                severity="HIGH",
                category="Moderation",
                recommendations={"action": "Review the complaint content. Consider temporary suspension of related accounts if necessary."},
                entity_id=db_complaint.complaint_id
            )
            
        if db_complaint.escalation_flag == "true":
            await trigger_notification(
                db=session,
                title="Automated Escalation",
                message=f"Incident {db_complaint.complaint_id} in {db_complaint.department} was automatically escalated.",
                severity="WARNING",
                category="Operations",
                recommendations={"action": f"Notify {db_complaint.department} head for urgent review."},
                entity_id=db_complaint.complaint_id
            )
            
    # 6. Insert into Qdrant
    qdrant_service.insert_complaint(text, category, vector, db_complaint.id)
    
    # 7. Broadcast update event via Websocket
    cluster_ids = [hit.payload.get("complaint_id") for hit in similar_complaints]
    update_event = {
        "event": "new_complaint",
        "data": {
            "id": db_complaint.id,
            "complaint_id": db_complaint.complaint_id,
            "text": text,
            "predicted_category": category,
            "similar_to": cluster_ids,
            "duplicate_group_id": assigned_cluster_id,
            "timestamp": db_complaint.timestamp.isoformat() if db_complaint.timestamp else None,
            "source": db_complaint.source,
            "department": db_complaint.department,
            "urgency_level": db_complaint.urgency_level,
            "sentiment_score": db_complaint.sentiment_score
        }
    }
    await manager.broadcast(update_event)
    logger.info(f"Processed and broadcasted complaint ID {db_complaint.id}")
    
    return db_complaint

async def process_message_with_retry(payload: dict):
    """Processes messages with retry limits and routes failures to DLQ"""
    retries = payload.get("retry_count", 0)
    try:
        await process_raw_message(payload)
    except Exception as e:
        logger.error(f"Execution failed for event {payload.get('complaint_id')}: {e}")
        from ingestion.kafka_producer import KafkaProducerManager
        try:
            producer = await KafkaProducerManager.get_producer()
            if retries < 3:
                payload["retry_count"] = retries + 1
                payload["last_error"] = str(e)
                await producer.send_and_wait(RETRY_TOPIC, payload)
                logger.info(f"Event {payload.get('complaint_id')} routed to retry queue.")
            else:
                payload["fatal_error"] = str(e)
                await producer.send_and_wait(DLQ_TOPIC, payload)
                logger.error(f"Event {payload.get('complaint_id')} exceeded max retries. Sent to DLQ.")
        except Exception as ex:
            logger.error(f"Failed to route message to recovery queue: {ex}")

async def consume_complaints():
    try:
        consumer = AIOKafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=False # Manual commits on processing success
        )
        await consumer.start()
        logger.info(f"Kafka Worker started. Listening on topic: {TOPIC}")
        
        try:
            async for msg in consumer:
                await process_message_with_retry(msg.value)
                await consumer.commit() # Commit offset only after retry routing succeeds
        finally:
            await consumer.stop()
    except Exception as e:
        logger.error(f"Kafka consumer error (Is Kafka running?): {e}")

if __name__ == "__main__":
    asyncio.run(consume_complaints())
