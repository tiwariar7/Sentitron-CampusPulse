import asyncio
import json
import logging
import sys
import os
import time
import uuid

# Ensure backend and ai-engine modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiokafka import AIOKafkaConsumer

# AI Imports
import sys
if "pytest" in sys.modules or os.getenv("TESTING") == "true":
    class MockClassifier:
        def classify(self, text): return "Other"
    classifier_pipeline = MockClassifier()
else:
    try:
        from ai_engine.classification.classifier import classifier_pipeline
    except ImportError as e:
        logging.error(f"Failed to load AI classifier: {e}")
        # Mock fallback for pure backend testing without heavy models
        class MockClassifier:
            def classify(self, text): return "Other"
        classifier_pipeline = MockClassifier()

from services.db import AsyncSessionLocal, Complaint, Setting
from api.routers.notifications import trigger_notification
from sqlalchemy.future import select
from ingestion.event_publisher import publish_complaint_classified

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC_COMPLAINTS", "complaint.created")
RETRY_TOPIC = TOPIC + "-retry"
DLQ_TOPIC = os.getenv("KAFKA_DLQ_PREFIX", "dlq") + ".complaint.created"
CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "campuspulse-workers")


async def process_raw_message(payload: dict, correlation_id: str) -> Complaint:
    """Processes a single raw complaint payload, runs classification, and inserts to DB."""
    complaint_id_str = payload.get("complaint_id")
    text = payload.get("complaint_text", "")
    
    if not text:
        return None
        
    logger.info(f"Worker processing raw complaint: {complaint_id_str} | correlation_id={correlation_id}")
    
    # 1. AI Classification & Latency calculation
    start_time = time.perf_counter()
    category = classifier_pipeline.classify(text)
    latency_ms = (time.perf_counter() - start_time) * 1000.0
    
    try:
        from ws_manager.manager import SYSTEM_METRICS
        SYSTEM_METRICS["last_inference_latency_ms"] = latency_ms
    except ImportError:
        pass
        
    # 2. Create database instance
    db_complaint = Complaint(
        complaint_id=complaint_id_str,
        source=payload.get("source", "Secure Portal"),
        department=payload.get("department", "Pending AI"),
        category=category,
        subcategory=payload.get("subcategory"),
        complaint_text=text,
        sentiment_score=payload.get("sentiment_score", 0.0),
        urgency_level=payload.get("urgency_level", 3),
        escalation_flag="true" if (payload.get("escalation_flag") == "true" or payload.get("urgency_level", 3) >= 4) else "false",
        resolved="false",
        duplicate_group_id=payload.get("duplicate_group_id") or f"CLUSTER_PENDING_{complaint_id_str}",
        toxicity_score=payload.get("toxicity_score", 0.0),
        anonymous=str(payload.get("anonymous", "true")),
        response_delay_hours=str(payload.get("response_delay_hours", "0"))
    )
    
    # 3. Atomic Write to Database
    async with AsyncSessionLocal() as session:
        session.add(db_complaint)
        await session.commit()
        await session.refresh(db_complaint)
        
        # 4. Toxicity & Escalation checking within processing transaction
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
                message=f"Incident {db_complaint.complaint_id} was automatically escalated due to high urgency.",
                severity="WARNING",
                category="Operations",
                recommendations={"action": f"Notify department head for urgent review."},
                entity_id=db_complaint.complaint_id
            )
            
    # 5. Publish to complaint.classified for downstream embedding & clustering
    classified_payload = {
        "db_id": db_complaint.id,
        "complaint_id": db_complaint.complaint_id,
        "complaint_text": text,
        "category": category,
        "urgency_level": db_complaint.urgency_level,
        "toxicity_score": db_complaint.toxicity_score,
        "source": db_complaint.source,
        "department": db_complaint.department,
        "sentiment_score": db_complaint.sentiment_score
    }
    
    await publish_complaint_classified(classified_payload, correlation_id=correlation_id)
    
    # 6. Broadcast update event via Websocket
    try:
        from ws_manager.manager import manager
        update_event = {
            "event": "new_complaint",
            "data": {
                "id": db_complaint.id,
                "complaint_id": db_complaint.complaint_id,
                "text": text,
                "predicted_category": category,
                "timestamp": db_complaint.timestamp.isoformat() if db_complaint.timestamp else None,
                "source": db_complaint.source,
                "department": db_complaint.department,
                "urgency_level": db_complaint.urgency_level,
                "sentiment_score": db_complaint.sentiment_score
            }
        }
        await manager.broadcast(update_event)
    except Exception as e:
        logger.warning(f"Failed to broadcast websocket event: {e}")
        
    return db_complaint


async def process_message_with_retry(envelope: dict):
    """Processes messages with retry limits and routes failures to DLQ"""
    payload = envelope.get("payload", {})
    correlation_id = envelope.get("correlation_id", str(uuid.uuid4()))
    retries = envelope.get("retry_count", 0)
    
    try:
        await process_raw_message(payload, correlation_id)
    except Exception as e:
        logger.error(f"Execution failed for event {payload.get('complaint_id')}: {e}")
        from ingestion.kafka_producer import KafkaProducerManager
        try:
            producer = await KafkaProducerManager.get_producer()
            if retries < 3:
                envelope["retry_count"] = retries + 1
                envelope["last_error"] = str(e)
                await producer.send_and_wait(RETRY_TOPIC, envelope)
                logger.info(f"Event {payload.get('complaint_id')} routed to retry queue.")
            else:
                envelope["fatal_error"] = str(e)
                await producer.send_and_wait(DLQ_TOPIC, envelope)
                logger.error(f"Event {payload.get('complaint_id')} exceeded max retries. Sent to DLQ.")
        except Exception as ex:
            logger.error(f"Failed to route message to recovery queue: {ex}")


async def consume_complaints():
    try:
        consumer = AIOKafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_BROKER,
            group_id=CONSUMER_GROUP,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=False  # Manual commits on processing success
        )
        await consumer.start()
        logger.info(f"Kafka Worker started. Listening on topic: {TOPIC}")
        
        try:
            async for msg in consumer:
                await process_message_with_retry(msg.value)
                await consumer.commit()  # Commit offset only after retry routing succeeds
        finally:
            await consumer.stop()
    except Exception as e:
        logger.error(f"Kafka consumer error (Is Kafka running?): {e}")


if __name__ == "__main__":
    asyncio.run(consume_complaints())
