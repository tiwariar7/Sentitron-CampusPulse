"""
Chaos & Failure Simulation.
Section 7 / Section 12 — Validates graceful degradation under fault injection.
"""
import asyncio
import httpx
import uuid
import random

API_BASE = "http://localhost:8000"


class ChaosSimulator:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=API_BASE, timeout=2.0)
        self.results = []

    async def inject_malformed_payload(self, count: int = 10):
        """Inject structurally invalid payloads — system must return 422, not crash."""
        print(f"\n--- Chaos: Malformed Payload Injection ({count} payloads) ---")
        malformed = [
            {"complaint_text": "only text"},
            {"complaint_id": "X", "toxicity_score": "not_a_number"},
            {},
            {"complaint_id": None, "urgency_level": -999},
            {"source": "x" * 10000},  # oversized field
        ]
        for i in range(count):
            payload = random.choice(malformed)
            try:
                res = await self.client.post("/ingestion/mock", json=payload)
                degraded_gracefully = res.status_code in (400, 422)
                self.results.append(("malformed", degraded_gracefully))
                print(f"  Payload {i+1}: {res.status_code} — {'✓ Graceful' if degraded_gracefully else '✗ Failed'}")
            except Exception as e:
                self.results.append(("malformed", False))
                print(f"  Payload {i+1}: Exception — {e}")

    async def simulate_burst_flood(self, count: int = 50):
        """Rapid-fire 50 concurrent requests — test queue saturation."""
        print(f"\n--- Chaos: Burst Flood ({count} concurrent requests) ---")

        async def send():
            cid = f"CHAOS-{uuid.uuid4().hex[:6].upper()}"
            payload = {
                "complaint_id": cid, "source": "Chaos", "department": "IT",
                "category": "Test", "subcategory": "Chaos",
                "complaint_text": "Chaos burst test complaint.",
                "sentiment_score": -0.1, "urgency_level": 1,
                "escalation_flag": "false", "resolved": "false",
                "duplicate_group_id": "", "toxicity_score": 5.0,
                "anonymous": "false", "response_delay_hours": "0",
            }
            try:
                res = await self.client.post("/ingestion/mock", json=payload, timeout=5.0)
                return res.status_code == 200
            except Exception:
                return False

        results = await asyncio.gather(*[send() for _ in range(count)])
        success = sum(results)
        rate = success / count
        print(f"  Burst flood: {success}/{count} OK ({rate:.1%})")
        self.results.append(("burst_flood", rate >= 0.95))

    async def simulate_invalid_websocket_payload(self):
        """Verify notification endpoint doesn't break on invalid action IDs."""
        print(f"\n--- Chaos: Invalid Notification Actions ---")
        for bad_id in [0, -1, 99999999, "abc"]:
            try:
                res = await self.client.post(f"/api/notifications/{bad_id}/acknowledge")
                ok = res.status_code in (404, 422)
                print(f"  ID={bad_id}: {res.status_code} — {'✓ Handled' if ok else '✗ Unhandled'}")
                self.results.append(("invalid_notif", ok))
            except Exception as e:
                print(f"  ID={bad_id}: Exception — {e}")
                self.results.append(("invalid_notif", False))

    async def simulate_unauthorized_config_write(self):
        """Attempt writes with low-privilege roles."""
        print(f"\n--- Chaos: Unauthorized Configuration Access ---")
        for role in ["Monitoring Viewer", "Department Admin", "Guest", ""]:
            res = await self.client.post(
                "/api/settings",
                json={"toxicity_threshold": 10},
                headers={"x-user-role": role},
            )
            blocked = res.status_code == 403
            print(f"  Role='{role}': {res.status_code} — {'✓ Blocked' if blocked else '✗ Allowed'}")
            self.results.append(("rbac", blocked))

    async def run_full_chaos_suite(self):
        print("="*50)
        print("  CHAOS & FAILURE SIMULATION SUITE")
        print("="*50)

        # Check backend is alive first
        try:
            health = await self.client.get("/health")
            if health.status_code != 200:
                print("Backend not running. Start FastAPI first.")
                return
        except Exception:
            print("Cannot connect to backend. Start FastAPI first.")
            return

        await self.inject_malformed_payload(count=5)
        await self.simulate_burst_flood(count=30)
        await self.simulate_invalid_websocket_payload()
        await self.simulate_unauthorized_config_write()

        total = len(self.results)
        passed = sum(1 for _, ok in self.results if ok)
        print(f"\n{'='*50}")
        print(f"  Chaos Results: {passed}/{total} scenarios handled gracefully")
        print(f"  Resilience Score: {passed/total:.1%}")
        print(f"{'='*50}")

        await self.client.aclose()


if __name__ == "__main__":
    sim = ChaosSimulator()
    asyncio.run(sim.run_full_chaos_suite())
