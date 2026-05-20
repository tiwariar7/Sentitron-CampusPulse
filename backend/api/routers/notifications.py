from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from services.db import get_db, Notification
from ws_manager.manager import notification_manager
from typing import Optional
import json

from services.auth import get_current_user, RoleChecker, User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@router.get("/")
async def get_notifications(
    severity: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == "guest":
        raise HTTPException(status_code=403, detail="Access denied: Guests cannot view notifications")
        
    query = select(Notification).order_by(Notification.timestamp.desc()).limit(limit)
    if severity:
        query = query.where(Notification.severity == severity)
    if state:
        query = query.where(Notification.lifecycle_state == state)
        
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    res = []
    for n in notifications:
        n_dict = {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "severity": n.severity,
            "category": n.category,
            "lifecycle_state": n.lifecycle_state,
            "timestamp": n.timestamp.isoformat() if n.timestamp else None,
            "related_entity_id": n.related_entity_id,
            "ai_recommendations": json.loads(n.ai_recommendations) if n.ai_recommendations else None
        }
        res.append(n_dict)
    return res

@router.post("/{notification_id}/acknowledge")
async def acknowledge_notification(
    notification_id: int,
    current_user: User = Depends(RoleChecker(["admin", "moderator"])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalars().first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.lifecycle_state = "ACKNOWLEDGED"
    await db.commit()
    return {"status": "success", "state": "ACKNOWLEDGED"}

@router.post("/{notification_id}/resolve")
async def resolve_notification(
    notification_id: int,
    current_user: User = Depends(RoleChecker(["admin", "moderator"])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalars().first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.lifecycle_state = "RESOLVED"
    await db.commit()
    return {"status": "success", "state": "RESOLVED"}

@router.post("/{notification_id}/dismiss")
async def dismiss_notification(
    notification_id: int,
    current_user: User = Depends(RoleChecker(["admin", "moderator"])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalars().first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.lifecycle_state = "DISMISSED"
    await db.commit()
    return {"status": "success", "state": "DISMISSED"}

async def trigger_notification(db: AsyncSession, title: str, message: str, severity: str, category: str, recommendations: dict = None, entity_id: str = None):
    notif = Notification(
        title=title,
        message=message,
        severity=severity,
        category=category,
        lifecycle_state="CREATED",
        ai_recommendations=json.dumps(recommendations) if recommendations else None,
        related_entity_id=entity_id
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    
    n_dict = {
        "id": notif.id,
        "title": notif.title,
        "message": notif.message,
        "severity": notif.severity,
        "category": notif.category,
        "lifecycle_state": notif.lifecycle_state,
        "timestamp": notif.timestamp.isoformat() if notif.timestamp else None,
        "related_entity_id": notif.related_entity_id,
        "ai_recommendations": json.loads(notif.ai_recommendations) if notif.ai_recommendations else None
    }
    
    await notification_manager.broadcast({
        "type": "NEW_NOTIFICATION",
        "notification": n_dict
    })
    
    return notif
