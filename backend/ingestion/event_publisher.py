"""
Typed event publisher for all domain events.
Wraps KafkaProducerManager with envelope schema v1.0.
Every event carries: event_id, event_type, schema_version, correlation_id, timestamp, payload.
Falls back to inline processing if Kafka is unavailable (circuit breaker open).
"""
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Topic names from environment (defaults match docker-compose.dev.yml kafka-init)
TOPIC_COMPLAINT_CREATED    = os.getenv("KAFKA_TOPIC_COMPLAINTS",    "complaint.created")
TOPIC_COMPLAINT_CLASSIFIED = os.getenv("KAFKA_TOPIC_CLASSIFIED",    "complaint.classified")
TOPIC_COMPLAINT_CLUSTERED  = os.getenv("KAFKA_TOPIC_CLUSTERED",     "complaint.clustered")
TOPIC_COMPLAINT_ESCALATED  = os.getenv("KAFKA_TOPIC_ESCALATED",     "complaint.escalated")
TOPIC_NOTIFICATION_CREATED = os.getenv("KAFKA_TOPIC_NOTIFICATION",  "notification.created")
TOPIC_AUDIT_LOGGED         = os.getenv("KAFKA_TOPIC_AUDIT",         "audit.logged")
TOPIC_ANALYTICS_GENERATED  = os.getenv("KAFKA_TOPIC_ANALYTICS",     "analytics.generated")


def _build_envelope(
    event_type: str,
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
    schema_version: str = "1.0",
) -> Dict[str, Any]:
    """Wrap payload in a standard event envelope."""
    return {
        "event_id":       str(uuid.uuid4()),
        "event_type":     event_type,
        "schema_version": schema_version,
        "correlation_id": correlation_id or str(uuid.uuid4()),
        "timestamp":      datetime.now(timezone.utc).isoformat(),
        "payload":        payload,
    }


async def _publish(topic: str, envelope: Dict[str, Any]) -> bool:
    """
    Publish envelope to Kafka topic.
    Returns True on success, False if Kafka unavailable (graceful degradation).
    """
    from utils.circuit_breaker import kafka_breaker, CircuitBreakerOpenError
    from ingestion.kafka_producer import KafkaProducerManager

    try:
        async with kafka_breaker:
            producer = await KafkaProducerManager.get_producer()
            await producer.send_and_wait(topic, envelope)
            logger.info(
                f"Published {envelope['event_type']} "
                f"[{envelope['event_id'][:8]}] → {topic}"
            )
            return True
    except CircuitBreakerOpenError as e:
        logger.warning(f"Kafka circuit OPEN — event {envelope['event_type']} dropped: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to publish to {topic}: {e}")
        return False


# ── Public API ──────────────────────────────────────────────────

async def publish_complaint_created(
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> bool:
    envelope = _build_envelope("complaint.created", payload, correlation_id)
    return await _publish(TOPIC_COMPLAINT_CREATED, envelope)


async def publish_complaint_classified(
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> bool:
    envelope = _build_envelope("complaint.classified", payload, correlation_id)
    return await _publish(TOPIC_COMPLAINT_CLASSIFIED, envelope)


async def publish_complaint_clustered(
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> bool:
    envelope = _build_envelope("complaint.clustered", payload, correlation_id)
    return await _publish(TOPIC_COMPLAINT_CLUSTERED, envelope)


async def publish_complaint_escalated(
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> bool:
    envelope = _build_envelope("complaint.escalated", payload, correlation_id)
    return await _publish(TOPIC_COMPLAINT_ESCALATED, envelope)


async def publish_notification_created(
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> bool:
    envelope = _build_envelope("notification.created", payload, correlation_id)
    return await _publish(TOPIC_NOTIFICATION_CREATED, envelope)


async def publish_audit_logged(
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> bool:
    envelope = _build_envelope("audit.logged", payload, correlation_id)
    return await _publish(TOPIC_AUDIT_LOGGED, envelope)


async def publish_analytics_generated(
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> bool:
    envelope = _build_envelope("analytics.generated", payload, correlation_id)
    return await _publish(TOPIC_ANALYTICS_GENERATED, envelope)
