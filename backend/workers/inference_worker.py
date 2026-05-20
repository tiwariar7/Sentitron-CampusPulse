"""
Standalone inference worker.
Consumes: complaint.classified
Runs:     embedding pipeline → Qdrant insert
Emits:    complaint.clustered
Uses:     Redis inference cache to skip redundant embeddings.
"""
import asyncio
import json
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

KAFKA_BROKER     = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_IN         = os.getenv("KAFKA_TOPIC_CLASSIFIED", "complaint.classified")
TOPIC_OUT        = os.getenv("KAFKA_TOPIC_CLUSTERED",  "complaint.clustered")
CONSUMER_GROUP   = os.getenv("KAFKA_CONSUMER_GROUP", "campuspulse-workers") + "-inference"
CONFIDENCE_THRESHOLD = float(os.getenv("INFERENCE_CONFIDENCE_THRESHOLD", "0.70"))

# Lazy imports for heavy AI deps
_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        try:
            from ai_engine.embeddings.embedder import embedder
            _embedder = embedder
        except ImportError:
            class _MockEmbedder:
                def embed(self, text): return [0.0] * 384
            _embedder = _MockEmbedder()
            logger.warning("Inference worker: using mock embedder (AI engine not available)")
    return _embedder


async def process_classified_event(envelope: dict, producer: AIOKafkaProducer) -> None:
    payload        = envelope.get("payload", {})
    complaint_id   = payload.get("complaint_id", "UNKNOWN")
    text           = payload.get("complaint_text", "")
    category       = payload.get("category", "Other")
    correlation_id = envelope.get("correlation_id")

    if not text:
        logger.warning(f"Empty text in classified event {complaint_id}")
        return

    # ── Redis cache check ────────────────────────────────────
    from services.redis_cache import redis_cache
    cached = await redis_cache.get_inference(text)

    if cached:
        vector = cached["vector"]
        logger.info(f"Inference cache HIT for {complaint_id}")
    else:
        from utils.circuit_breaker import qdrant_breaker
        embedder = _get_embedder()
        vector   = embedder.embed(text)
        await redis_cache.set_inference(text, {"vector": vector, "category": category})
        logger.info(f"Inference computed and cached for {complaint_id}")

    # ── Qdrant insert ────────────────────────────────────────
    try:
        from utils.circuit_breaker import qdrant_breaker, CircuitBreakerOpenError
        from services.qdrant_service import qdrant_service
        async with qdrant_breaker:
            similar = qdrant_service.find_similar(vector, limit=5, score_threshold=0.85)
            qdrant_service.insert_complaint(text, category, vector, payload.get("db_id"))
        cluster_ids = [h.payload.get("complaint_id") for h in similar]
    except Exception as e:
        logger.error(f"Qdrant error for {complaint_id}: {e}")
        similar    = []
        cluster_ids = []

    # ── Emit complaint.clustered ─────────────────────────────
    from ingestion.event_publisher import _build_envelope
    out_payload  = {**payload, "similar_complaint_ids": cluster_ids}
    out_envelope = _build_envelope("complaint.clustered", out_payload, correlation_id)
    await producer.send_and_wait(TOPIC_OUT, json.dumps(out_envelope).encode())
    logger.info(f"Emitted complaint.clustered for {complaint_id} — {len(cluster_ids)} similar found")


async def run_inference_worker():
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKER)
    consumer = AIOKafkaConsumer(
        TOPIC_IN,
        bootstrap_servers=KAFKA_BROKER,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    await producer.start()
    await consumer.start()
    logger.info(f"Inference worker started. Topic: {TOPIC_IN} → {TOPIC_OUT}")

    try:
        async for msg in consumer:
            try:
                await process_classified_event(msg.value, producer)
                await consumer.commit()
            except Exception as e:
                logger.error(f"Inference worker error: {e}")
                await consumer.commit()  # Don't reblock on poison messages
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(run_inference_worker())
