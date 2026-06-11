<div align="center">

# 🧠 Enterprise Knowledge Copilot

**A production-oriented RAG platform for internal documents, tickets, SOPs, wikis, and PDFs.**

Ask questions in natural language and get grounded, cited answers from your own knowledge base — with multi-tenant isolation, role-based access control, and a full audit trail.

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white">
  <img alt="Redis" src="https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white">
  <img alt="OpenTelemetry" src="https://img.shields.io/badge/OpenTelemetry-traces-425CC7?logo=opentelemetry&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-Proprietary-lightgrey">
</p>

</div>

---

## ✨ Highlights

| | Capability | Description |
|---|---|---|
| 🔐 | **Multi-tenant auth** | JWT-based authentication with per-tenant request scoping |
| 👥 | **Workspaces + RBAC** | Workspace membership and role-based access control on every action |
| 📄 | **Versioned ingestion** | S3 upload → document versioning → chunking with rich metadata |
| 🔎 | **Hybrid retrieval** | Dense vector search (pgvector) blended with keyword scoring, plus reranking |
| 📌 | **Citation tracking** | Every answer maps back to specific chunks, pages, and source locations |
| ✅ | **Answer verification** | Grounding checks with an abstain/refuse policy for unsupported claims |
| 📝 | **Audit logging** | Every query and answer is persisted with provenance and verdict |
| 📊 | **Observability** | OpenTelemetry traces + Prometheus metrics out of the box |

---

## 🚀 Quickstart

### Option 1 — Backend only (recommended for local development)

```bash
cd backend
pip install poetry
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2 — Full stack (Postgres + Redis + API)

The repo ships with a `docker-compose.yml` that brings up `pgvector`, Redis, and the API together.

```bash
docker compose up --build
```

### Verify it's running

| Endpoint | Purpose |
|---|---|
| http://localhost:8000/health | Sanity check → `{"status":"ok"}` |
| http://localhost:8000/docs | Interactive Swagger UI |
| http://localhost:8000/metrics | Prometheus metrics |

---

## 🗺️ How it works

```
                        ┌──────────────┐
   Upload  ──────────▶  │  Ingestion   │  S3 → version → chunk → embed → pgvector
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
   Question ─────────▶  │  Retrieval   │  dense + keyword → hybrid rank → rerank
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │ Verification │  grounding check → abstain if unsupported
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
   Answer  ◀──────────  │  Citations   │  [1][2]… mapped to chunks + locations
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │    Audit     │  persist query, evidence, verdict
                        └──────────────┘
```

Every request passes three trust gates:

- **Authorization gate** — requests are scoped to a `workspace_id`; RBAC enforces who can read, upload, or query.
- **Evidence gate** — verification must find grounding for claims, otherwise the system abstains.
- **Audit gate** — every query and answer is persisted with provenance and verdict.

See [`docs/architecture-overview.md`](docs/architecture-overview.md) for the full design.

---

## 📚 API overview

Base URL (dev): `http://localhost:8000`

### Auth — `/auth`
| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Obtain a JWT |

### Workspaces — `/api/v1/workspaces`
| Method | Path | Description |
|---|---|---|
| `POST` | `/` | Create a workspace |
| `GET` | `/` | List workspaces |
| `GET` | `/{workspace_id}` | Get a workspace |
| `PATCH` | `/{workspace_id}` | Update a workspace |
| `DELETE` | `/{workspace_id}` | Delete a workspace |
| `GET` | `/{workspace_id}/members` | List members |
| `POST` | `/{workspace_id}/members` | Add a member |
| `PATCH` | `/{workspace_id}/members/{user_id}` | Update a member's role |
| `DELETE` | `/{workspace_id}/members/{user_id}` | Remove a member |

### Ingestion — `/api/v1/workspaces`
| Method | Path | Description |
|---|---|---|
| `POST` | `/{workspace_id}/documents/upload` | Upload a document |
| `GET` | `/{workspace_id}/documents` | List documents |
| `GET` | `/{workspace_id}/documents/{document_id}` | Get a document |
| `DELETE` | `/{workspace_id}/documents/{document_id}` | Delete a document |
| `POST` | `/{workspace_id}/documents/ingest` | Trigger chunking + embedding |
| `GET` | `/{workspace_id}/documents/{document_id}/chunks` | List chunks |

### Query — `/api/v1/workspaces`
| Method | Path | Description |
|---|---|---|
| `POST` | `/{workspace_id}/query` | Ask a question and receive a grounded, cited answer |

Full request/response examples live in [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md).

---

## ⚙️ Configuration

Copy the example env file and fill in your values:

```bash
cp backend/.env.example backend/.env
```

Key settings:

| Variable | Purpose |
|---|---|
| `JWT_SECRET` / `JWT_ALGORITHM` / `JWT_EXP_SECONDS` | JWT signing and expiry |
| `PGVECTOR_DSN` | PostgreSQL + pgvector connection string |
| `REDIS_URL` | Redis connection string |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | Embedding / LLM provider |
| `S3_BUCKET` / `S3_REGION` / `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` | Object storage for documents |
| `OTEL_SERVICE_NAME` / `PROMETHEUS_PATH` | Observability |

---

## 🧱 Repo layout

```
enterprise-knowledge-copilot/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── auth/            # JWT auth + dependencies
│   │   ├── multitenancy/    # Tenant context + request scoping
│   │   ├── rbac/            # Role-based access control
│   │   ├── workspaces/      # Workspace + membership management
│   │   ├── ingestion/       # Upload, versioning, chunking
│   │   ├── rag/             # Embeddings, retrieval, rerank, citations, verification
│   │   ├── query/           # Query endpoint
│   │   ├── audit/           # Audit log persistence
│   │   ├── observability/   # OpenTelemetry + Prometheus
│   │   ├── storage/         # S3 integration
│   │   ├── db/              # SQLAlchemy models + migrations
│   │   └── main.py          # App entrypoint
│   └── tests/               # Unit + integration tests
├── docs/                    # Architecture + API documentation
└── docker-compose.yml       # Postgres (pgvector) + Redis + API
```

---

## 🧪 Testing

```bash
cd backend
poetry run pytest
```

---

## 📦 Tech stack

**FastAPI** · **SQLAlchemy 2** · **PostgreSQL + pgvector** · **Redis** · **PyJWT** · **OpenAI** · **boto3 (S3)** · **OpenTelemetry** · **Prometheus**

---