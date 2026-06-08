# API Documentation — Enterprise Knowledge Copilot (Backend)

> Note: This is an evolving API document matching the current scaffolding in this repo.
> As endpoints are implemented, update this doc.

## Base URL

- Development: `http://localhost:8000`

## Authentication

- JWT auth is expected for protected endpoints.
- Multi-tenant requests are scoped by `workspace_id`.

## Health

### `GET /health`
- Response: `{ "status": "ok" }`

## Metrics

### `GET /metrics`
- Prometheus metrics endpoint

## Workspaces

> See server routers under `backend/app/workspaces/router.py` and `backend/app/multitenancy/*`.

## Ingestion

> Document ingestion endpoints are scaffolded under `backend/app/ingestion/router.py`.

### Expected Ingestion Workflow
1. Create a document upload/version (per workspace)
2. Chunk content with metadata (page/section/offset)
3. Generate embeddings
4. Upsert chunk embeddings into pgvector

## Query (Planned)

### `POST /rag/query`

**Request body (planned)**
```json
{
  "workspace_id": 123,
  "query": "...",
  "top_k": 10,
  "alpha": 0.5
}
```

**Response (planned)**
```json
{
  "answer": "..." ,
  "verdict": "grounded|ungrounded",
  "citations": [
    {
      "citation_id": "[1]",
      "document_id": 1,
      "version_id": 7,
      "chunk_index": 3,
      "score": 0.92,
      "source_location": "section:10-240"
    }
  ]
}
```
