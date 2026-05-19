from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import sys
import os

# Add parent directory to path so we can import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import ComplaintCreate, ComplaintResponse
from services.db import Complaint, get_db

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

@router.post("/mock", response_model=ComplaintResponse)
async def ingest_mock_complaint(complaint_data: ComplaintCreate, db: AsyncSession = Depends(get_db)):
    """
    Mock ingestion endpoint to receive student complaints from various streams.
    This simulates data coming from WhatsApp, Forms, etc.
    """
    # Create the db model instance
    db_complaint = Complaint(
        student_id=complaint_data.student_id,
        category=complaint_data.category,
        content=complaint_data.content,
        source=complaint_data.source,
        status="PENDING"
    )
    
    db.add(db_complaint)
    await db.commit()
    await db.refresh(db_complaint)
    
    # In a real system, we would push to Kafka here
    # For Stage 1, we just save to DB
    
    return db_complaint
