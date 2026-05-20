import csv
import random
from datetime import datetime, timedelta
import uuid

# Configuration
NUM_RECORDS = 3500
START_DATE = datetime(2026, 2, 1)
END_DATE = datetime(2026, 5, 1)

SOURCES = ["WhatsApp", "Form", "Email", "Anonymous Report", "App"]
SOURCE_WEIGHTS = [0.4, 0.2, 0.2, 0.1, 0.1]

DEPARTMENTS = ["CSE", "ECE", "ME", "CE", "EEE", "MBA", "Common"]
DEP_WEIGHTS = [0.4, 0.2, 0.1, 0.1, 0.05, 0.05, 0.1]

CATEGORIES = [
    ("Academic", 0.30),
    ("Infrastructure", 0.20),
    ("Hostel", 0.15),
    ("Placement", 0.15),
    ("Training", 0.10),
    ("Faculty", 0.05),
    ("Administration", 0.02),
    ("Transport", 0.01),
    ("Mental Wellness", 0.01),
    ("Harassment", 0.01)
]
CAT_NAMES = [c[0] for c in CATEGORIES]
CAT_WEIGHTS = [c[1] for c in CATEGORIES]

# Incident templates mapping to subcategories and templates
INCIDENT_TEMPLATES = {
    "WIFI_OUTAGE_LIBRARY": {
        "category": "Infrastructure",
        "subcategory": "Network",
        "templates": [
            "The Wi-Fi in the main library has been down for three days now.",
            "library wifi is completely dead. Please fix it ASAP.",
            "wifi firse gaya 😭 library me",
            "No internet connection in the library again.",
            "library me net nahi chal raha kab thik hoga",
            "Unable to access internet in library",
            "library network outage since morning"
        ],
        "urgency_range": (3, 5),
        "escalation_prob": 0.3
    },
    "MESS_FOOD_POISONING": {
        "category": "Hostel",
        "subcategory": "Food Hygiene",
        "templates": [
            "Mess food quality in hostel B has deteriorated significantly.",
            "Found a bug in my salad at the main cafeteria.",
            "mess ka khana bahut kharab hai, log beemar pad rahe hain",
            "Food quality in the mess has degraded significantly.",
            "I got food poisoning after eating dinner yesterday.",
            "stale food served in hostel B dinner",
            "mess food is unhygienic and causing health issues"
        ],
        "urgency_range": (4, 5),
        "escalation_prob": 0.8
    },
    "TRAINING_TOC_MISMATCH": {
        "category": "Training",
        "subcategory": "Curriculum",
        "templates": [
            "The Java trainer skipped scheduled topics.",
            "Topics outside the official TOC are being taught.",
            "Socket programming was introduced unexpectedly.",
            "The trainer is not following the announced syllabus.",
            "Trainer is rushing through JDBC concepts.",
            "training ka pace bahut fast hai kuch samajh nahi aa raha",
            "topics skipped by placement trainer today"
        ],
        "urgency_range": (2, 4),
        "escalation_prob": 0.4
    },
    "FACULTY_ATTENDANCE": {
        "category": "Academic",
        "subcategory": "Attendance",
        "templates": [
            "Faculty attendance policy bahut unfair hai.",
            "My attendance was marked absent even though I was present.",
            "Professor missed the last three lectures without prior notice.",
            "Prof hasn't shown up for classes this whole week.",
            "attendance portal is showing wrong data for CS101",
            "attendance issue in DBMS class",
            "teacher not coming but taking attendance online??"
        ],
        "urgency_range": (2, 3),
        "escalation_prob": 0.1
    },
    "TRANSPORT_BUS_DELAY": {
        "category": "Transport",
        "subcategory": "Bus Delay",
        "templates": [
            "Bus route 4 is delayed by 45 minutes.",
            "bus 4 fir late ayi",
            "We are waiting at the stop for 1 hour for the college bus.",
            "Transport facility is very poor, bus never comes on time.",
            "driver of bus 7 is very rude",
            "bus breakdown on highway again"
        ],
        "urgency_range": (2, 4),
        "escalation_prob": 0.2
    },
    "PLACEMENT_INTERVIEW_CLASH": {
        "category": "Placement",
        "subcategory": "Scheduling",
        "templates": [
            "TCS interview clashes with my final exam.",
            "placement drive and mid sem on same day??",
            "Please reschedule the Infosys pre-placement talk.",
            "Interview slots are overlapping for multiple companies.",
            "HR round postponed without notice",
            "placement cell is not responding to mails"
        ],
        "urgency_range": (4, 5),
        "escalation_prob": 0.7
    },
    "EXAM_SCHEDULE_ISSUE": {
        "category": "Academic",
        "subcategory": "Exams",
        "templates": [
            "The CS101 final exam schedule conflicts with the MA201 exam.",
            "Need to reschedule the database systems exam.",
            "exam schedule is too tight, no prep leaves",
            "2 exams on the same day is unfair",
            "mid sem dates are clashing with technical fest",
            "syllabus for exams not declared yet"
        ],
        "urgency_range": (3, 5),
        "escalation_prob": 0.5
    },
    "HOSTEL_WATER_ISSUE": {
        "category": "Hostel",
        "subcategory": "Water",
        "templates": [
            "There is no hot water in Block B hostels since yesterday.",
            "Block B geysers are not working, we need hot water.",
            "water cooler in Block C is dispensing dirty water.",
            "no drinking water on 3rd floor",
            "paani nahi aa raha subah se",
            "plumber not fixing the leaking tap in room 204"
        ],
        "urgency_range": (3, 4),
        "escalation_prob": 0.2
    },
    "HARASSMENT_REPORT": {
        "category": "Harassment",
        "subcategory": "Bullying",
        "templates": [
            "Seniors are ragging in the hostel block.",
            "Facing toxic behavior from a faculty member.",
            "constant bullying by batchmates",
            "Anonymous harassment on college group",
            "Please take action against ragging in boys hostel"
        ],
        "urgency_range": (5, 5),
        "escalation_prob": 0.95
    },
    "FEE_ISSUE": {
        "category": "Administration",
        "subcategory": "Fees",
        "templates": [
            "Late fee was charged wrongly on my account.",
            "Scholarship disbursement is delayed by 2 months.",
            "fee portal is down, last date tomorrow",
            "extra charges in this semester fee structure?",
            "refund not processed yet"
        ],
        "urgency_range": (3, 4),
        "escalation_prob": 0.3
    }
}

# Generate 250 dummy incident clusters
clusters = []
for i in range(250):
    base_template = random.choice(list(INCIDENT_TEMPLATES.keys()))
    cluster_id = f"{base_template}_{i}"
    
    # Random burst time for this cluster
    delta = END_DATE - START_DATE
    random_days = random.randrange(delta.days)
    burst_center = START_DATE + timedelta(days=random_days)
    
    clusters.append({
        "cluster_id": cluster_id,
        "base": INCIDENT_TEMPLATES[base_template],
        "burst_center": burst_center
    })

def generate_record(cluster):
    base = cluster["base"]
    
    # Time around burst center (within 48 hours)
    time_offset = timedelta(hours=random.uniform(-24, 24))
    timestamp = cluster["burst_center"] + time_offset
    
    text = random.choice(base["templates"])
    
    # Introduce typos sometimes
    if random.random() < 0.1:
        text = text.replace("e", "ee", 1).replace("a", "", 1).lower()
        
    urgency = random.randint(base["urgency_range"][0], base["urgency_range"][1])
    is_escalated = "true" if random.random() < base["escalation_prob"] else "false"
    is_resolved = "true" if random.random() > 0.4 else "false"
    sentiment = round(random.uniform(0.1, 0.4), 2) # mostly negative
    toxicity = round(random.uniform(0.0, 0.3) if base["category"] != "Harassment" else random.uniform(0.6, 0.9), 2)
    
    return [
        f"CMP-{uuid.uuid4().hex[:8].upper()}",
        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        random.choices(SOURCES, SOURCE_WEIGHTS)[0],
        random.choices(DEPARTMENTS, DEP_WEIGHTS)[0],
        base["category"],
        base["subcategory"],
        text,
        sentiment,
        urgency,
        is_escalated,
        is_resolved,
        cluster["cluster_id"],
        toxicity,
        "true" if random.random() < 0.2 else "false",
        random.randint(1, 48) if is_resolved == "true" else ""
    ]

# Generate records
records = []
for _ in range(NUM_RECORDS):
    # Pick a random cluster, favoring some to be huge bursts and some to be small
    cluster = random.choice(clusters)
    records.append(generate_record(cluster))

# Sort by timestamp
records.sort(key=lambda x: datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S"))

# Write to CSV
headers = [
    "complaint_id", "timestamp", "source", "department", "category", 
    "subcategory", "complaint_text", "sentiment_score", "urgency_level", 
    "escalation_flag", "resolved", "duplicate_group_id", "toxicity_score", 
    "anonymous", "response_delay_hours"
]

with open("d:/Sentitron-CampusPulse/datasets/campuspulse_stream_dataset.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(records)

print(f"Generated {NUM_RECORDS} records in campuspulse_stream_dataset.csv")
