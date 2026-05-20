from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from services.db import get_db, Complaint
from api.routers.notifications import trigger_notification

from services.auth import RoleChecker, User

router = APIRouter(prefix="/api/clusters", tags=["clusters"])

@router.get("/active")
async def get_active_clusters(
    current_user: User = Depends(RoleChecker(["admin", "moderator"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the top active semantic clusters.
    Uses an aggregate join query to eliminate N+1 relational loops.
    """
    # 1. Compile subquery to extract group statistics and representative row IDs (minimum ID)
    subq = select(
        Complaint.duplicate_group_id,
        func.count(Complaint.id).label("count"),
        func.max(Complaint.urgency_level).label("max_urgency"),
        func.min(Complaint.id).label("rep_id")
    ).filter(Complaint.duplicate_group_id != "", Complaint.duplicate_group_id.is_not(None))\
     .group_by(Complaint.duplicate_group_id)\
     .subquery()
     
    # 2. Main query to join stats back to Complaint table to fetch representative content details
    stmt = select(
        subq.c.duplicate_group_id,
        subq.c.count,
        subq.c.max_urgency,
        Complaint.complaint_text,
        Complaint.category
    ).join(Complaint, Complaint.id == subq.c.rep_id)\
     .order_by(subq.c.count.desc())\
     .limit(10)
     
    result = await db.execute(stmt)
    rows = result.all()
    
    clusters = []
    for row in rows:
        group_id, count, max_urgency, rep_text, category = row
        
        clusters.append({
            "cluster_id": group_id,
            "incident_count": count,
            "max_urgency": max_urgency,
            "representative_text": rep_text,
            "category": category
        })
        
        # Operational Alert Trigger if cluster count scales
        if count >= 5:
            await trigger_notification(
                db=db,
                title="Rapid Cluster Growth Detected",
                message=f"Semantic cluster '{group_id}' has rapidly accumulated {count} incidents in {category}.",
                severity="HIGH",
                category="Clustering",
                recommendations={"action": f"Investigate root cause for cluster {group_id}."},
                entity_id=group_id
            )
        
    return clusters
