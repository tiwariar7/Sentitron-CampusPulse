import asyncio
import httpx
import random
import uuid

API_BASE = "http://localhost:8000"

class VerificationSimulator:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=API_BASE)

    async def inject_toxicity_surge(self, count=5):
        print(f"--- Injecting Toxicity Surge ({count} incidents) ---")
        for i in range(count):
            payload = {
                "complaint_id": f"SIM-TOX-{uuid.uuid4().hex[:4].upper()}",
                "source": "Simulator",
                "department": "Security",
                "category": "Harassment",
                "subcategory": "Verbal",
                "complaint_text": f"This is an incredibly toxic simulated message {i}!!",
                "sentiment_score": -0.9,
                "urgency_level": 3,
                "escalation_flag": "false",
                "resolved": "false",
                "duplicate_group_id": "",
                "toxicity_score": random.uniform(85.0, 99.0), # Triggers Toxicity Threshold
                "anonymous": "true",
                "response_delay_hours": "0"
            }
            res = await self.client.post("/ingestion/mock", json=payload)
            print(f"Injected: {payload['complaint_id']} -> {res.status_code}")
            await asyncio.sleep(0.5)

    async def inject_cluster_growth(self, count=6):
        print(f"--- Injecting Rapid Cluster Growth ({count} incidents) ---")
        cluster_id = f"C-SIM-{uuid.uuid4().hex[:4].upper()}"
        for i in range(count):
            payload = {
                "complaint_id": f"SIM-CLU-{uuid.uuid4().hex[:4].upper()}",
                "source": "Simulator",
                "department": "Hostel",
                "category": "Maintenance",
                "subcategory": "Plumbing",
                "complaint_text": f"Water is leaking from the roof in block A again. Iteration {i}",
                "sentiment_score": -0.6,
                "urgency_level": 2,
                "escalation_flag": "false",
                "resolved": "false",
                "duplicate_group_id": cluster_id, # Same cluster
                "toxicity_score": 10.0,
                "anonymous": "false",
                "response_delay_hours": "0"
            }
            res = await self.client.post("/ingestion/mock", json=payload)
            print(f"Injected: {payload['complaint_id']} -> {res.status_code}")
            await asyncio.sleep(0.5)
            # Make a call to /api/clusters/active to trigger the notification check
            await self.client.get("/api/clusters/active")

    async def inject_critical_anonymous(self):
        print(f"--- Injecting Critical Anonymous Incident ---")
        payload = {
            "category": "Emergency",
            "description": "Simulated critical security incident near campus gate.",
            "urgency": "Critical"
        }
        res = await self.client.post("/api/incidents/anonymous", json=payload)
        print(f"Injected Anonymous Critical -> {res.status_code}")
        
    async def trigger_forecasting_anomaly(self):
        print(f"--- Triggering Forecasting Anomaly ---")
        # Repeatedly call trends until it randomly hits >85 risk and triggers a notification
        for i in range(10):
            res = await self.client.get("/api/forecasting/trends")
            if res.json().get("surge_risk_probability", 0) > 85:
                print(f"Anomaly Triggered -> {res.status_code}")
                break
            await asyncio.sleep(0.5)

    async def run_smoke_test(self):
        print("Starting Verification Simulator Smoke Test...")
        await self.inject_toxicity_surge(count=2)
        await asyncio.sleep(1)
        await self.inject_cluster_growth(count=6)
        await asyncio.sleep(1)
        await self.inject_critical_anonymous()
        await asyncio.sleep(1)
        await self.trigger_forecasting_anomaly()
        print("Simulation Complete.")

if __name__ == "__main__":
    sim = VerificationSimulator()
    asyncio.run(sim.run_smoke_test())
