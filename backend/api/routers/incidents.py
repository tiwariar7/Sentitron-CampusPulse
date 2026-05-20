from fastapi import APIRouter, Depends, Query, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, or_
from services.db import get_db, Complaint, User
from api.routers.notifications import trigger_notification
from services.auth import get_current_user, get_optional_current_user, RoleChecker
from pydantic import BaseModel
import uuid
from typing import Optional

from ingestion.event_publisher import (
    publish_complaint_created,
    publish_complaint_escalated,
)

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

class AnonymousReport(BaseModel):
    category: str
    description: str
    urgency: str

class AuthenticatedReport(BaseModel):
    category: str
    subcategory: str
    description: str
    urgency: str
    department: str

@router.get("/")
async def get_incidents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, le=100),
    offset: int = 0
):
    # Enforce RBAC filtering
    if current_user.role in ["admin", "moderator"]:
        stmt = select(Complaint).order_by(desc(Complaint.timestamp)).offset(offset).limit(limit)
    elif current_user.role == "user":
        # Standard User sees their own reports plus public reports (anonymous="false")
        stmt = (
            select(Complaint)
            .where(or_(Complaint.reported_by_id == current_user.id, Complaint.anonymous == "false"))
            .order_by(desc(Complaint.timestamp))
            .offset(offset)
            .limit(limit)
        )
    else:
        # Guests or limited users cannot retrieve general feeds
        raise HTTPException(status_code=403, detail="Access denied: Guests cannot view the raw incident feed")
        
    result = await db.execute(stmt)
    complaints = result.scalars().all()
    return complaints

@router.post("/anonymous")
async def submit_anonymous(
    report: AnonymousReport,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Determine urgency level
    urgency_map = {"Standard": 3, "High": 4, "Critical": 5}
    urgency = urgency_map.get(report.urgency, 3)
    
    # We do NOT save reported_by_id to keep it completely anonymous
    db_complaint = Complaint(
        complaint_id=f"ANON-{uuid.uuid4().hex[:6].upper()}",
        source="Secure Portal",
        department="Pending AI",
        category=report.category,
        subcategory="TBD",
        complaint_text=report.description,
        sentiment_score=0.1,
        urgency_level=urgency,
        escalation_flag="true" if urgency >= 4 else "false",
        resolved="false",
        duplicate_group_id="",
        toxicity_score=0.0,
        anonymous="true",
        response_delay_hours="0"
    )
    db.add(db_complaint)
    await db.commit()
    await db.refresh(db_complaint)

    # Publish to Kafka event pipeline (non-blocking)
    correlation_id = str(uuid.uuid4())
    await publish_complaint_created(
        payload={
            "complaint_id":   db_complaint.complaint_id,
            "complaint_text": report.description,
            "category":       report.category,
            "department":     "Pending AI",
            "urgency_level":  urgency,
            "anonymous":      "true",
            "source":         "Secure Portal",
        },
        correlation_id=correlation_id,
    )

    if urgency >= 4:
        severity = "CRITICAL" if urgency == 5 else "HIGH"
        await trigger_notification(
            db=db,
            title="Anonymous High-Urgency Report",
            message=f"A new anonymous report requires immediate attention in {report.category}.",
            severity=severity,
            category="Security",
            recommendations={"action": "Dispatch campus security or relevant authority immediately."},
            entity_id=db_complaint.complaint_id
        )
        # Trigger email worker via Kafka
        await publish_complaint_escalated(
            payload={
                "complaint_id":   db_complaint.complaint_id,
                "department":     "Pending AI",
                "severity":       severity,
                "complaint_text": report.description,
            },
            correlation_id=correlation_id,
        )

    return {"status": "submitted", "id": db_complaint.complaint_id, "correlation_id": correlation_id}

@router.post("/report")
async def submit_report(
    report: AuthenticatedReport,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Determine urgency level
    urgency_map = {"Standard": 3, "High": 4, "Critical": 5}
    urgency = urgency_map.get(report.urgency, 3)
    
    db_complaint = Complaint(
        complaint_id=f"CMP-{uuid.uuid4().hex[:6].upper()}",
        source="Secure Portal",
        department=report.department,
        category=report.category,
        subcategory=report.subcategory,
        complaint_text=report.description,
        sentiment_score=0.1,
        urgency_level=urgency,
        escalation_flag="true" if urgency >= 4 else "false",
        resolved="false",
        duplicate_group_id="",
        toxicity_score=0.0,
        anonymous="false",
        response_delay_hours="0",
        reported_by_id=current_user.id
    )
    db.add(db_complaint)
    await db.commit()
    await db.refresh(db_complaint)
    
    if urgency >= 4:
        severity = "CRITICAL" if urgency == 5 else "HIGH"
        await trigger_notification(
            db=db,
            title=f"New High-Urgency Report",
            message=f"A new report has been submitted by {current_user.username} in {report.category}.",
            severity=severity,
            category="Security",
            recommendations={"action": "Dispatch security or contact department supervisor immediately."},
            entity_id=db_complaint.complaint_id
        )
    
    return {"status": "submitted", "id": db_complaint.complaint_id}
