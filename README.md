# 🎓 Sentitron CampusPulse

> **Real-Time AI Campus Intelligence & Escalation Platform**

Sentitron CampusPulse is an enterprise-grade, full-stack operational intelligence system designed for educational institutions. It ingests, classifies, clusters, and escalates campus incidents and complaints in real time — surfacing actionable insights to administrators, moderators, faculty, students, and guests through a role-aware dashboard.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔐 **Multi-Role RBAC** | JWT-secured authentication with four roles: Admin, Moderator, User, Guest |
| 📡 **Real-Time WebSockets** | Live dashboard updates and push notifications over WebSocket channels |
| 🤖 **AI Classification** | NLP-powered incident classification and severity scoring |
| 🧩 **Semantic Clustering** | Vector-embedding-based incident deduplication via Qdrant |
| 📈 **Predictive Forecasting** | Time-series trend forecasting on complaint patterns |
| 🔔 **Notification Engine** | Lifecycle-aware notifications (Created → Acknowledged → Resolved/Dismissed) |
| 📊 **Analytics Dashboard** | Department-wise breakdown, urgency heatmaps, and KPI cards |
| 🗂️ **Audit Logs** | Full administrator action audit trail |
| 📥 **Kafka Ingestion** | Async Kafka-based event ingestion with mock fallback |
| 🐳 **Docker Infrastructure** | Containerised Postgres, Qdrant, Zookeeper, and Kafka |
| 📝 **Anonymous Reporting** | Guest-accessible anonymous complaint submission portal |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js 16)                   │
│  Dashboard · Incidents · Clusters · Analytics · Reports     │
│  Forecasting · Monitoring · Notifications · Settings        │
│                      (localhost:3000)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │  REST + WebSocket
┌─────────────────────────▼───────────────────────────────────┐
│               BACKEND (FastAPI + Uvicorn)                   │
│  Auth · Incidents · Clusters · Analytics · Monitoring       │
│  Forecasting · Notifications · Settings · Ingestion         │
│                      (localhost:8000)                       │
└───────┬────────────────┬─────────────────┬──────────────────┘
        │                │                 │
┌───────▼──────┐ ┌───────▼──────┐ ┌───────▼──────┐
│  SQLite /    │ │    Qdrant    │ │    Kafka     │
│  PostgreSQL  │ │  (Vectors)   │ │  (Streaming) │
│  port 5432   │ │  port 6333   │ │  port 9092   │
└──────────────┘ └──────────────┘ └──────────────┘
        │
┌───────▼──────────────────────────────────────────┐
│                  AI ENGINE                       │
│  Classification · Embeddings · Escalation        │
│  Summarization · Forecasting                     │
└──────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Sentitron-CampusPulse/
├── backend/                    # FastAPI backend
│   ├── api/
│   │   ├── main.py             # App entry point, lifespan, middleware, WebSocket endpoints
│   │   └── routers/            # Feature routers
│   │       ├── auth.py         # JWT login, /me, user listing
│   │       ├── incidents.py    # Complaint CRUD & ingestion
│   │       ├── clusters.py     # Semantic cluster queries
│   │       ├── analytics.py    # Aggregated analytics
│   │       ├── monitoring.py   # System health metrics
│   │       ├── forecasting.py  # Trend prediction
│   │       ├── notifications.py# Notification lifecycle management
│   │       └── settings.py     # Platform configuration
│   ├── ingestion/
│   │   ├── kafka_producer.py   # Shared Kafka producer pool
│   │   ├── kafka_worker.py     # Async Kafka consumer & processing
│   │   └── mock_ingestion.py   # HTTP fallback ingestion endpoint
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response schemas
│   ├── services/
│   │   ├── db.py               # SQLAlchemy async models (User, Complaint, Notification, AuditLog, Setting)
│   │   ├── auth.py             # Password hashing (bcrypt), JWT creation/verification
│   │   └── qdrant_service.py   # Qdrant vector store client
│   ├── ws_manager/
│   │   └── manager.py          # WebSocket connection managers (dashboard + notifications)
│   ├── scripts/
│   │   ├── seed_db_direct.py   # Offline DB seeder (32 accounts across 4 roles)
│   │   └── seed_accounts.py    # API-based account seeder
│   ├── campuspulse.db          # SQLite database (dev default)
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # Next.js 16 + TypeScript frontend
│   └── src/
│       ├── app/                # Next.js App Router pages
│       │   ├── auth/           # Login page
│       │   ├── dashboard/      # Main KPI dashboard
│       │   ├── incidents/      # Incident feed & detail
│       │   ├── clusters/       # Semantic incident clusters
│       │   ├── analytics/      # Charts & department breakdowns
│       │   ├── forecasting/    # Trend forecasting charts
│       │   ├── monitoring/     # System health (admin only)
│       │   ├── notifications/  # Notification centre
│       │   ├── reports/        # Report generation
│       │   └── settings/       # Platform settings (admin only)
│       ├── components/         # Shared UI components
│       ├── context/            # React context providers
│       └── lib/                # API client utilities
│
├── ai-engine/                  # AI/ML processing modules
│   ├── classification/         # Incident category & severity classifier
│   ├── embeddings/             # Sentence-embedding generation
│   ├── escalation/             # Escalation logic & thresholds
│   ├── summarization/          # Incident summarization
│   └── forecasting/            # Time-series forecasting
│
├── tests/                      # Pytest test suites (async)
│   ├── security/
│   │   ├── test_auth_rbac.py   # RBAC role-boundary tests
│   │   └── test_abuse.py       # Rate-limit & abuse tests
│   ├── clustering/
│   ├── forecasting/
│   ├── governance/
│   ├── infrastructure/
│   ├── ingestion/
│   ├── intelligence/
│   ├── monitoring/
│   ├── reliability/
│   └── websocket/
│
├── infrastructure/
│   ├── docker/
│   │   └── docker-compose.yml  # Postgres, Qdrant, Zookeeper, Kafka
│   ├── grafana/                # Grafana dashboards
│   ├── kafka/                  # Kafka topic configs
│   └── prometheus/             # Prometheus scrape configs
│
├── verification/               # V&V framework
├── datasets/                   # Sample complaint datasets
├── docs/                       # Additional documentation
├── pytest.ini                  # Pytest asyncio configuration
└── test_accounts.txt           # Seeded credential reference sheet
```

---

## 🔐 Role-Based Access Control (RBAC)

The platform enforces four distinct roles via JWT claims:

| Role | Access Level |
|---|---|
| **Admin** | Full access — dashboard, incidents, clusters, analytics, forecasting, monitoring, settings, notifications, reports, audit logs, user management |
| **Moderator** | Incidents, clusters, analytics, forecasting, notifications, reports. Cannot access: monitoring, settings, audit logs, user management |
| **User** | Dashboard, own incidents, notifications, reports. Cannot access: clusters, analytics, forecasting, monitoring, settings, audit logs |
| **Guest** | Read-only dashboard + anonymous reporting portal only |

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology |
|---|---|
| API Framework | **FastAPI** + Uvicorn |
| ORM | **SQLAlchemy** (async) |
| Database | **SQLite** (dev) / **PostgreSQL** (prod) |
| Vector Store | **Qdrant** |
| Message Broker | **Apache Kafka** (aiokafka) |
| Authentication | **JWT** (PyJWT) + **bcrypt** (passlib) |
| AI/ML | **HuggingFace Transformers**, **Sentence-Transformers**, **PyTorch** |

### Frontend
| Layer | Technology |
|---|---|
| Framework | **Next.js 16** (App Router) |
| Language | **TypeScript** |
| Styling | **Tailwind CSS v4** |
| Charts | **Recharts** |
| Animation | **Framer Motion** |
| Icons | **Lucide React** |

### Infrastructure
| Service | Purpose |
|---|---|
| Docker Compose | Container orchestration |
| PostgreSQL 15 | Production relational database |
| Qdrant | Vector similarity search |
| Apache Kafka | Async event streaming |
| Prometheus | Metrics collection |
| Grafana | Metrics visualisation |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (for full infrastructure)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/Sentitron-CampusPulse.git
cd Sentitron-CampusPulse
```

### 2. Start Infrastructure Services (Optional — for Kafka & Qdrant)

```bash
docker-compose -f infrastructure/docker/docker-compose.yml up -d
```

### 3. Set Up the Backend

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r backend/requirements.txt

# Start the FastAPI server
cd backend
uvicorn api.main:app --reload --port 8000
```

> The backend will auto-create the SQLite database and seed a default `admin` user on first start.

### 4. Seed All Test Accounts (Optional)

```bash
# Offline seeder — works without API running
python backend/scripts/seed_db_direct.py

# API-based seeder — requires the backend to be running
python backend/scripts/seed_accounts.py
```

### 5. Set Up the Frontend

```bash
cd frontend
npm install
npm run dev
```

The application will be available at **http://localhost:3000**.

---

## 🔑 Default Credentials

> Refer to `test_accounts.txt` for the full list of 32 seeded accounts (8 per role).

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@Secure1` |
| Admin | `superadmin` | `SuperAdmin@2` |
| Moderator | `mod_cse` | `Mod_CSE@1` |
| User | `student_arjun` | `Arjun@Student1` |
| Guest | `visitor_1` | `Visitor@Gst1` |

---

## 📡 API Reference

**Base URL:** `http://localhost:8000`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Service health check |
| `POST` | `/api/auth/login` | None | Obtain JWT access token |
| `GET` | `/api/auth/me` | Bearer | Get current user profile |
| `GET` | `/api/auth/users` | Admin | List all users |
| `GET` | `/api/incidents` | User+ | Fetch incident feed |
| `POST` | `/api/incidents` | User+ | Submit new incident |
| `GET` | `/api/clusters` | Mod+ | Semantic incident clusters |
| `GET` | `/api/analytics` | Mod+ | Aggregated analytics data |
| `GET` | `/api/forecasting` | Mod+ | Complaint trend forecasts |
| `GET` | `/api/monitoring` | Admin | System health metrics |
| `GET` | `/api/notifications` | User+ | Notification centre |
| `GET` | `/api/settings` | Admin | Platform settings |
| `WS` | `/ws/dashboard` | — | Real-time dashboard feed |
| `WS` | `/ws/notifications` | — | Real-time push notifications |

**Interactive API Docs:** http://localhost:8000/docs (Swagger UI)

### Quick Login Example

```bash
# Get a token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@Secure1"}'

# Use the token
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

---

## 🧪 Testing

The project includes a comprehensive async test suite organised by domain:

```bash
# Run all tests
pytest

# Run specific test domains
pytest tests/security/          # RBAC & abuse tests
pytest tests/clustering/        # Semantic clustering tests
pytest tests/ingestion/         # Kafka ingestion tests
pytest tests/reliability/       # Load & chaos tests
pytest tests/websocket/         # WebSocket tests
```

> All tests use `asyncio_mode = auto` (configured in `pytest.ini`).

---

## 🗄️ Database Models

| Model | Table | Description |
|---|---|---|
| `User` | `users` | Platform users with role, department, and bcrypt password |
| `Complaint` | `complaints` | Campus incidents with sentiment score, urgency, escalation flags |
| `Notification` | `notifications` | Lifecycle-tracked alerts (CREATED → ACKNOWLEDGED → RESOLVED) |
| `Setting` | `settings` | Key-value platform configuration store |
| `AuditLog` | `audit_logs` | Admin action history with before/after state tracking |

---

## 🌐 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./campuspulse.db` | Async database URL |
| `SECRET_KEY` | *(set in auth service)* | JWT signing secret |

For production, point `DATABASE_URL` to your PostgreSQL instance:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/campuspulse
```

---

## 📜 License

This project is developed for academic and institutional use under the Sentitron initiative.

---

> Built with ❤️ by the Sentitron team — *Turning campus noise into actionable intelligence.*
