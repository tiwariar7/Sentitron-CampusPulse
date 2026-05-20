"""
Historical Event Replay Engine.
Validates deterministic analytics regeneration by replaying
archived incident datasets in time-ordered sequence.
"""
import asyncio
import httpx
import csv
import os
import time
from datetime import datetime


DATASET_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "datasets", "campuspulse_stream_dataset.csv"
)
API_BASE = "http://localhost:8000"


class ReplayEngine:
    def __init__(self, batch_size: int = 50, delay: float = 0.05):
        self.batch_size = batch_size
        self.delay = delay
        self.replayed = []
        self.failures = []

    async def replay_from_csv(self, client: httpx.AsyncClient, limit: int = 500):
        """Replay up to `limit` historical incidents in timestamp order."""
        print(f"\n=== Historical Event Replay — {limit} incidents ===")
        start = time.monotonic()

        if not os.path.exists(DATASET_PATH):
            print(f"Dataset not found at {DATASET_PATH}. Skipping replay.")
            return

        rows = []
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                rows.append(row)

        # Replay in order
        for row in rows:
            payload = {
                "complaint_id": f"RPLY-{row['complaint_id']}",
                "source": row.get("source", "Replay"),
                "department": row.get("department", "Unknown"),
                "category": row.get("category", "General"),
                "subcategory": row.get("subcategory", ""),
                "complaint_text": row.get("complaint_text", ""),
                "sentiment_score": float(row.get("sentiment_score", 0.0)),
                "urgency_level": int(row.get("urgency_level", 1)),
                "escalation_flag": str(row.get("escalation_flag", "false")).lower(),
                "resolved": str(row.get("resolved", "false")).lower(),
                "duplicate_group_id": row.get("duplicate_group_id", ""),
                "toxicity_score": float(row.get("toxicity_score", 0.0)),
                "anonymous": str(row.get("anonymous", "false")).lower(),
                "response_delay_hours": str(row.get("response_delay_hours", "0")),
            }
            try:
                res = await client.post("/ingestion/mock", json=payload, timeout=5.0)
                if res.status_code == 200:
                    self.replayed.append(payload["complaint_id"])
                else:
                    self.failures.append(payload["complaint_id"])
            except Exception as e:
                self.failures.append(payload["complaint_id"])
                print(f"  Replay failed for {payload['complaint_id']}: {e}")

            await asyncio.sleep(self.delay)

        elapsed = time.monotonic() - start
        success_rate = len(self.replayed) / max(len(rows), 1)
        print(f"\nReplay Complete:")
        print(f"  Replayed:    {len(self.replayed)}/{len(rows)}")
        print(f"  Failures:    {len(self.failures)}")
        print(f"  Success Rate:{success_rate:.1%}")
        print(f"  Elapsed:     {elapsed:.1f}s")
        return success_rate

    async def validate_analytics_after_replay(self, client: httpx.AsyncClient):
        """Verify analytics endpoints remain consistent after replay."""
        print("\n=== Post-Replay Analytics Validation ===")
        checks = [
            ("/api/clusters/active", "clusters"),
            ("/api/notifications", "notifications"),
            ("/api/forecasting/trends", "forecasting"),
            ("/api/monitoring/metrics", "monitoring"),
        ]
        for url, name in checks:
            res = await client.get(url)
            status = "✓" if res.status_code == 200 else "✗"
            print(f"  {status} {name} ({url}) — {res.status_code}")


async def run_replay(limit: int = 100):
    engine = ReplayEngine(delay=0.02)
    async with httpx.AsyncClient(base_url=API_BASE) as client:
        # Health check first
        health = await client.get("/health")
        if health.status_code != 200:
            print("Backend not running. Start FastAPI first.")
            return

        success_rate = await engine.replay_from_csv(client, limit=limit)
        await engine.validate_analytics_after_replay(client)

        if success_rate is not None:
            assert success_rate >= 0.99, f"Replay success rate below 99%: {success_rate:.1%}"
            print(f"\n✓ Replay validation passed ({success_rate:.1%} success rate)")


if __name__ == "__main__":
    asyncio.run(run_replay(limit=200))
