"""
Analytics publisher daemon.
Periodically aggregates metrics from the database and publishes snapshots
to the analytics.generated Kafka topic.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.future import select
from sqlalchemy import func
from services.db import AsyncSessionLocal, Complaint
from ingestion.event_publisher import publish_analytics_generated

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PUBLISH_INTERVAL = int(os.getenv("ANALYTICS_PUBLISH_INTERVAL_SECONDS", "60"))


async def generate_analytics_snapshot() -> dict:
    """Query the DB for current key performance/operational indicators."""
    async with AsyncSessionLocal() as session:
        # Total complaints count
        total_stmt = select(func.count(Complaint.id))
        total_res  = await session.execute(total_stmt)
        total_count = total_res.scalar() or 0

        # Unresolved/pending complaints count
        unresolved_stmt = select(func.count(Complaint.id)).where(Complaint.resolved == False)
        unresolved_res  = await session.execute(unresolved_stmt)
        unresolved_count = unresolved_res.scalar() or 0

        # Breakdown by category
        category_stmt = select(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category)
        category_res  = await session.execute(category_stmt)
        categories    = {row[0]: row[1] for row in category_res.all() if row[0]}

        # Breakdown by department
        dept_stmt = select(Complaint.department, func.count(Complaint.id)).group_by(Complaint.department)
        dept_res  = await session.execute(dept_stmt)
        departments = {row[0]: row[1] for row in dept_res.all() if row[0]}

        # High/Critical urgency count
        escalated_stmt = select(func.count(Complaint.id)).where(Complaint.urgency_level >= 4)
        escalated_res  = await session.execute(escalated_stmt)
        escalated_count = escalated_res.scalar() or 0

        return {
            "timestamp":        datetime.now(timezone.utc).isoformat(),
            "total_complaints": total_count,
            "unresolved_count": unresolved_count,
            "escalated_count":  escalated_count,
            "by_category":      categories,
            "by_department":    departments,
        }


async def run_analytics_loop():
    logger.info(f"Analytics publisher started. Interval: {PUBLISH_INTERVAL}s")
    while True:
        try:
            snapshot = await generate_analytics_snapshot()
            success  = await publish_analytics_generated(snapshot)
            if success:
                logger.info(f"Published analytics snapshot: total={snapshot['total_complaints']}")
        except Exception as e:
            logger.error(f"Failed to generate/publish analytics snapshot: {e}")
        
        await asyncio.sleep(PUBLISH_INTERVAL)


if __name__ == "__main__":
    asyncio.run(run_analytics_loop())
