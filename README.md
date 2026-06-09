# Enterprise Knowledge Copilot

Production-oriented RAG system for internal documents, tickets, SOPs, wikis, and PDFs.

## What this backend provides

- **Multi-tenant auth (JWT)**
- **Workspace membership + RBAC**
- **Document ingestion with versioning**
- **Chunking + embeddings + hybrid retrieval + reranking**
- **Citation tracking (chunk/page level)**
- **Answer verification & grounding**
- **Audit logs for every query and answer**
- **Observability** (OpenTelemetry + Prometheus metrics)

## Quickstart

> See `backend/README.md` for backend-specific instructions.

### 1) Run the backend only (recommended for local development)

From the repo root:

```bash
cd backend
pip install poetry
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:
- `http://localhost:8000/health` (sanity check)
- `http://localhost:8000/metrics` (Prometheus)

### 2) Run the full stack (Postgres + backend + Redis)

This repo includes `docker-compose.yml`.

From the repo root:

```bash
docker compose up --build
```

## Environment variables

Example settings live in:
- `backend/.env.example`

Key values used by the backend include:
- `PGVECTOR_DSN`
- `REDIS_URL`
- `JWT_SECRET` (or `jwt_secret` depending on env mapping)
- OpenAI/LLM configuration (e.g. `OPENAI_API_KEY`, `OPENAI_MODEL`)

## Repo layout

- `backend/` - FastAPI application
- `docs/` - architecture + API docs
- `backend/tests/` - unit/integration tests