from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from services.db import get_db, Complaint
import datetime

from services.auth import RoleChecker, User

router = APIRouter(prefix="/api/forecasting", tags=["forecasting"])

@router.get("/trends")
async def get_trends(
    current_user: User = Depends(RoleChecker(["admin", "moderator"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Computes real operational forecasts.
    Calculates surge risk based on complaint volume growth trends,
    confidence limits on database size, and flags the highest-volume category as target.
    """
    # 1. Total incidents in DB
    total_res = await db.execute(select(func.count(Complaint.id)))
    total_count = total_res.scalar() or 0
    
    # 2. Incidents in the last 24 hours (IST timezone offset matching db.py default fallback)
    limit_time = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30) - datetime.timedelta(hours=24)
    recent_res = await db.execute(select(func.count(Complaint.id)).where(Complaint.timestamp >= limit_time))
    recent_count = recent_res.scalar() or 0
    
    # 3. Calculate surge risk probability based on incident acceleration
    # Baseline: if we have 0 complaints, surge risk is low (e.g. 10%).
    # If recent complaints form a large percentage of total complaints, risk increases.
    if total_count == 0:
        surge_risk = 10
    else:
        # acceleration coefficient
        ratio = recent_count / max(total_count, 1)
        surge_risk = min(int(10 + ratio * 150), 98)
        
    # Calculate confidence based on volume of data points
    confidence = min(int(60 + (total_count * 2)), 99)
    
    # Predict the most active category as the predicted surge cluster
    cat_stmt = select(Complaint.category, func.count(Complaint.id))\
        .group_by(Complaint.category)\
        .order_by(func.count(Complaint.id).desc())\
        .limit(1)
    cat_res = await db.execute(cat_stmt)
    cat_row = cat_res.first()
    predicted_cluster = cat_row[0] if cat_row else "Hostel Maintenance"
    
    return {
        "surge_risk": surge_risk,
        "confidence": confidence,
        "predicted_cluster": predicted_cluster,
        "historical_volume": total_count,
        "recent_24h_volume": recent_count
    }
