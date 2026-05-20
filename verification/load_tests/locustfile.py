"""
Locust load test — Operational Stress Verification.
Run with: locust -f verification/load_tests/locustfile.py --host=http://localhost:8000

Simulates:
- Concurrent incident ingestion burst (500–2000 users)
- Concurrent notification reads (WebSocket fanout proxy via HTTP)
- Settings governance reads
"""
import uuid
import random
from locust import HttpUser, task, between


DEPARTMENTS = ["Hostel", "IT", "Placement", "Academic", "Security", "Canteen"]
CATEGORIES = ["Maintenance", "Network", "Safety", "Academics", "Food", "Harassment"]


class IncidentIngestor(HttpUser):
    """Simulates concurrent student complaint ingestion."""
    wait_time = between(0.1, 0.5)

    @task(5)
    def ingest_complaint(self):
        payload = {
            "complaint_id": f"LCST-{uuid.uuid4().hex[:8].upper()}",
            "source": random.choice(["WhatsApp", "Portal", "Email", "Form"]),
            "department": random.choice(DEPARTMENTS),
            "category": random.choice(CATEGORIES),
            "subcategory": "General",
            "complaint_text": random.choice([
                "WiFi is down again in the hostel.",
                "Placement sessions are too rushed and unorganized.",
                "Canteen food quality has deteriorated severely.",
                "Hostel ceiling is leaking since past 3 days.",
                "wifi firse gaya 😭 kuch nahi hota yaha",  # Hinglish
                "This is absolutely unacceptable, disgusting service!!",
            ]),
            "sentiment_score": round(random.uniform(-1.0, 0.5), 2),
            "urgency_level": random.randint(1, 5),
            "escalation_flag": random.choice(["true", "false"]),
            "resolved": "false",
            "duplicate_group_id": random.choice(["G-001", "G-002", "G-003", ""]),
            "toxicity_score": round(random.uniform(0.0, 100.0), 1),
            "anonymous": random.choice(["true", "false"]),
            "response_delay_hours": str(random.randint(0, 72)),
        }
        self.client.post("/ingestion/mock", json=payload, name="/ingestion/mock [complaint]")

    @task(3)
    def read_incident_feed(self):
        self.client.get("/api/incidents", name="/api/incidents [feed]")

    @task(2)
    def read_clusters(self):
        self.client.get("/api/clusters/active", name="/api/clusters/active [clustering]")

    @task(2)
    def read_notifications(self):
        self.client.get("/api/notifications", name="/api/notifications [command-center]")

    @task(1)
    def read_forecasting(self):
        self.client.get("/api/forecasting/trends", name="/api/forecasting/trends [anomaly]")

    @task(1)
    def read_monitoring(self):
        self.client.get("/api/monitoring/metrics", name="/api/monitoring/metrics [infra]")

    @task(1)
    def read_settings(self):
        self.client.get("/api/settings", headers={"x-user-role": "Monitoring Viewer"},
                        name="/api/settings [governance]")


class AnonymousReporter(HttpUser):
    """Simulates anonymous high-urgency report submissions."""
    wait_time = between(1.0, 3.0)

    @task
    def submit_anonymous_report(self):
        self.client.post("/api/incidents/anonymous", json={
            "category": random.choice(["Security", "Harassment", "Emergency", "General"]),
            "description": "Locust-simulated anonymous operational report.",
            "urgency": random.choice(["Standard", "High", "Critical"]),
        }, name="/api/incidents/anonymous [report]")
