from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from services.db import get_db, Complaint

from services.auth import RoleChecker, User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/health")
async def get_health_analytics(
    current_user: User = Depends(RoleChecker(["admin", "moderator"])),
    db: AsyncSession = Depends(get_db)
):
    # Department breakdown
    dep_stmt = select(Complaint.department, func.count(Complaint.id)).group_by(Complaint.department)
    dep_res = await db.execute(dep_stmt)
    dep_data = [{"name": row[0] if row[0] else "Unknown", "incidents": row[1]} for row in dep_res.all()]
    
    # Source breakdown
    src_stmt = select(Complaint.source, func.count(Complaint.id)).group_by(Complaint.source)
    src_res = await db.execute(src_stmt)
    src_data = [{"name": row[0] if row[0] else "Unknown", "value": row[1]} for row in src_res.all()]
    
    # Total critical
    crit_stmt = select(func.count(Complaint.id)).filter(Complaint.urgency_level >= 4)
    crit_res = await db.execute(crit_stmt)
    critical_count = crit_res.scalar()
    
    return {
        "departments": dep_data,
        "sources": src_data,
        "critical_escalations": critical_count or 0
    }
