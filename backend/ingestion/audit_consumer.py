"""
Audit event consumer.
Consumes: audit.logged
Writes: AuditLog table (immutable append-only)
"""
import asyncio
import json
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiokafka import AIOKafkaConsumer
from services.db import AsyncSessionLocal, AuditLog

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

KAFKA_BROKER   = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_AUDIT    = os.getenv("KAFKA_TOPIC_AUDIT", "audit.logged")
CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "campuspulse-workers") + "-audit"


async def run_audit_consumer():
    consumer = AIOKafkaConsumer(
        TOPIC_AUDIT,
        bootstrap_servers=KAFKA_BROKER,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )
    await consumer.start()
    logger.info(f"Audit consumer started on topic: {TOPIC_AUDIT}")

    try:
        async for msg in consumer:
            envelope = msg.value
            payload  = envelope.get("payload", {})

            try:
                async with AsyncSessionLocal() as session:
                    record = AuditLog(
                        administrator_identity=payload.get("administrator_identity", "system"),
                        user_id=payload.get("user_id"),
                        action=payload.get("action", "UNKNOWN"),
                        modified_parameters=json.dumps(payload.get("modified_parameters", {})),
                        previous_values=json.dumps(payload.get("previous_values", {})),
                        updated_values=json.dumps(payload.get("updated_values", {})),
                    )
                    session.add(record)
                    await session.commit()
                logger.info(
                    f"Audit record written: action={payload.get('action')} "
                    f"correlation={envelope.get('correlation_id', '')[:8]}"
                )
                await consumer.commit()
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(run_audit_consumer())
