from fastapi import APIRouter, Depends
import sys
import os
import uuid
import datetime
import logging

# Add parent directory to path so we can import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import ComplaintCreate, ComplaintResponse
from ingestion.kafka_producer import KafkaProducerManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingestion", tags=["ingestion"])

@router.post("/mock", response_model=ComplaintResponse)
async def ingest_mock_complaint(complaint_data: ComplaintCreate):
    """
    Ingestion endpoint to receive student complaints from various streams.
    Decoupled from DB persistence to ensure high-throughput event queue buffering.
    """
    complaint_id = complaint_data.complaint_id or f"CMP-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.datetime.utcnow()
    
    # Construct raw payload dictionary for serialization
    payload = {
        "complaint_id": complaint_id,
        "source": complaint_data.source,
        "department": complaint_data.department,
        "category": complaint_data.category,
        "subcategory": complaint_data.subcategory,
        "complaint_text": complaint_data.complaint_text,
        "sentiment_score": complaint_data.sentiment_score,
        "urgency_level": complaint_data.urgency_level,
        "escalation_flag": complaint_data.escalation_flag,
        "resolved": complaint_data.resolved,
        "duplicate_group_id": complaint_data.duplicate_group_id,
        "toxicity_score": complaint_data.toxicity_score,
        "anonymous": complaint_data.anonymous,
        "response_delay_hours": complaint_data.response_delay_hours,
        "timestamp": timestamp.isoformat()
    }
    
    db_id = 0 # Placeholder for queued messages
    
    try:
        # Publish payload to Kafka using the shared producer
        producer = await KafkaProducerManager.get_producer()
        await producer.send_and_wait("complaints", payload)
        logger.info(f"Published raw complaint {complaint_id} to event stream.")
    except Exception as e:
        logger.warning(f"Kafka broker unavailable, falling back to direct background processing: {e}")
        try:
            # Inline processing callback to maintain standalone execution capabilities
            from ingestion.kafka_worker import process_raw_message
            saved_complaint = await process_raw_message(payload)
            if saved_complaint:
                db_id = saved_complaint.id
        except Exception as inner_e:
            logger.error(f"Direct processing fallback failed: {inner_e}")
            
    return ComplaintResponse(
        id=db_id,
        complaint_id=complaint_id,
        timestamp=timestamp,
        source=complaint_data.source,
        department=complaint_data.department,
        category=complaint_data.category,
        subcategory=complaint_data.subcategory,
        complaint_text=complaint_data.complaint_text,
        sentiment_score=complaint_data.sentiment_score,
        urgency_level=complaint_data.urgency_level,
        escalation_flag=complaint_data.escalation_flag,
        resolved=complaint_data.resolved,
        duplicate_group_id=complaint_data.duplicate_group_id,
        toxicity_score=complaint_data.toxicity_score,
        anonymous=complaint_data.anonymous,
        response_delay_hours=complaint_data.response_delay_hours
    )
