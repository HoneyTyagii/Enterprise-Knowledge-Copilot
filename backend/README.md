# Enterprise Knowledge Copilot Backend (FastAPI)

## Quickstart

### 1) Requirements
- Python 3.11+

### 2) Install dependencies

```bash
cd backend
pip install poetry
poetry install
```

### 3) Run
```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Notes
This is a production-oriented scaffold. Implementations for:
- JWT auth + multi-tenant + RBAC
- S3 ingestion + document versioning
- Chunking + embeddings + pgvector hybrid retrieval
- Reranking + citations
- Grounding/verification
- Audit logs
- OpenTelemetry + Prometheus

are to be added incrementally.

