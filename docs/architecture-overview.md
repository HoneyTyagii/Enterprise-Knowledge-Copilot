# Architecture Overview — Enterprise Knowledge Copilot

Production-oriented RAG system with:
- Multi-tenant JWT + RBAC authorization
- Document ingestion with versioning
- Hybrid retrieval (dense vector + keyword score)
- Citation tracking per retrieved chunk
- Answer verification / grounding with abstain policy
- Audit logs for every query/answer
- Observability: OpenTelemetry traces + Prometheus metrics

## High-level flow

### 1) Ingestion
1. Client uploads document to **S3**
2. Backend creates a **document version** for `(workspace_id, document_id, version_id)`
3. Chunking produces `document_chunks` with metadata (`section_path`, `page`, `char_start`, `char_end`, etc.)
4. Embeddings are generated for each chunk
5. Embeddings are upserted into **pgvector** (`document_vectors`) by `(workspace_id, document_id, version_id, chunk_index)`

### 2) Query / Retrieval / Answer
1. Request is authorized via JWT + RBAC
2. Hybrid retrieval:
   - Dense retrieval from pgvector to get candidate chunks
   - Keyword scoring on candidate chunk content
   - Hybrid score ranks final retrieved chunks
3. (Later) Reranking: cross-encoder / LLM judge reranks retrieved chunks
4. Citations:
   - Each retrieved chunk is mapped to a citation id like `[1]`
   - Chunk metadata is converted into source locations
5. Verification:
   - Grounding checks whether the answer is supported by retrieved evidence
   - If ungrounded, system abstains/refuses with a safe response
6. Audit:
   - Persist query + retrieved chunk ids + draft/final answers + verdict + grounding details
7. Observability:
   - Emit traces for each stage
   - Emit Prometheus metrics (latency, counts, grounding failures)

## Key packages/modules (backend/app)

- `app/multitenancy/*`
  - Tenant context, request scoping helpers
- `app/rbac/*`
  - RBAC policy + request dependencies
- `app/ingestion/*`
  - Document versioning + chunking
- `app/rag/*`
  - `embeddings.py`: embedding interface
  - `vector_store.py`: pgvector schema + upsert
  - `pipeline.py`: embed + upsert pipeline
  - `retrieval.py`: hybrid retrieval + scoring
  - `rerank.py`: reranking scaffold
  - `citations.py`: citation creation from retrieved chunks
  - `source_mapping.py`: metadata -> location string
  - `verification.py` / `answer_verification.py`: grounding & abstain policy
  - `audit_integration.py`: audit log persistence integration with RAG
- `app/audit/*`
  - DB persistence for query/answer audits
- `app/observability/*`
  - Prometheus metrics + OpenTelemetry tracing bootstrap

## Data model (conceptual)
- `organizations` / `workspaces` / `workspace_members`
- `documents`, `document_versions`
- `document_chunks` (content + metadata)
- `document_vectors` (pgvector embeddings)
- `query_audit_logs`

## Trust boundaries
- Authorization gate:
  - Every ingestion and query is scoped to `workspace_id`
  - RBAC enforces which roles may read/upload/query
- Evidence gate:
  - Verification must find grounding evidence for claims
  - Abstain/refuse on ungrounded results
- Audit gate:
  - Every query/answer is persisted with provenance and verdict
