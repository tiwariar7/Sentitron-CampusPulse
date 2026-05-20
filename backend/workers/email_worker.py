"""
Kafka consumer worker for email dispatch.
Consumes: complaint.escalated, notification.created
Dispatches: Gmail SMTP via EmailService
Routes failures to dlq.email topic after max retries.
"""
import asyncio
import json
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiokafka import AIOKafkaConsumer
from services.email_service import email_service
from services.db import AsyncSessionLocal
from utils.circuit_breaker import email_breaker, CircuitBreakerOpenError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

KAFKA_BROKER         = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_ESCALATED      = os.getenv("KAFKA_TOPIC_ESCALATED", "complaint.escalated")
TOPIC_NOTIFICATION   = os.getenv("KAFKA_TOPIC_NOTIFICATION", "notification.created")
DLQ_EMAIL            = os.getenv("KAFKA_DLQ_PREFIX", "dlq") + ".email"
CONSUMER_GROUP       = os.getenv("KAFKA_CONSUMER_GROUP", "campuspulse-workers") + "-email"


async def handle_escalation_event(payload: dict, db) -> bool:
    """Send escalation alert email. Returns True on success."""
    complaint_id = payload.get("complaint_id", "UNKNOWN")
    department   = payload.get("department", "Unknown")
    severity     = payload.get("severity", "HIGH")
    description  = payload.get("complaint_text", payload.get("description", "No description"))

    try:
        async with email_breaker:
            result = await email_service.send_escalation_alert(
                complaint_id=complaint_id,
                department=department,
                severity=severity,
                description=description,
                db=db,
            )
        if result["status"] == "sent":
            logger.info(f"Escalation email sent for {complaint_id}")
            return True
        else:
            logger.error(f"Escalation email failed for {complaint_id}: {result['error']}")
            return False
    except CircuitBreakerOpenError as e:
        logger.warning(f"Email circuit OPEN — skipping {complaint_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unhandled error sending escalation email for {complaint_id}: {e}")
        return False


async def handle_notification_event(payload: dict, db) -> bool:
    """Send notification digest email for admin-level notifications."""
    severity = payload.get("severity", "INFO")
    # Only email for HIGH/CRITICAL notifications to avoid spam
    if severity not in ("HIGH", "CRITICAL"):
        return True

    try:
        async with email_breaker:
            result = await email_service.send_system_alert(
                alert_name=payload.get("title", "System Notification"),
                severity=severity,
                description=payload.get("message", ""),
                db=db,
            )
        return result["status"] == "sent"
    except CircuitBreakerOpenError:
        return False
    except Exception as e:
        logger.error(f"Notification email error: {e}")
        return False


async def route_to_dlq(producer, payload: dict, error: str) -> None:
    """Send unrecoverable event to dead-letter queue."""
    try:
        payload["dlq_reason"] = error
        await producer.send_and_wait(
            DLQ_EMAIL,
            json.dumps(payload).encode("utf-8"),
        )
        logger.error(f"Event routed to DLQ: {DLQ_EMAIL}")
    except Exception as e:
        logger.critical(f"Failed to write to DLQ: {e}")


async def run_email_worker():
    """Main email worker loop."""
    from aiokafka import AIOKafkaProducer

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    consumer = AIOKafkaConsumer(
        TOPIC_ESCALATED,
        TOPIC_NOTIFICATION,
        bootstrap_servers=KAFKA_BROKER,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    await producer.start()
    await consumer.start()
    logger.info(f"Email worker started. Topics: {TOPIC_ESCALATED}, {TOPIC_NOTIFICATION}")

    try:
        async for msg in consumer:
            payload = msg.value
            topic   = msg.topic
            success = False

            async with AsyncSessionLocal() as db:
                if topic == TOPIC_ESCALATED:
                    success = await handle_escalation_event(payload, db)
                elif topic == TOPIC_NOTIFICATION:
                    success = await handle_notification_event(payload, db)

            if success:
                await consumer.commit()
            else:
                await route_to_dlq(producer, payload, f"Processing failed for topic {topic}")
                await consumer.commit()  # Don't reprocess poison messages
    finally:
        await consumer.stop()
        await producer.stop()
        logger.info("Email worker shut down.")


if __name__ == "__main__":
    asyncio.run(run_email_worker())
