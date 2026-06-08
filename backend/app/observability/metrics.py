from __future__ import annotations

from prometheus_client import Counter, Histogram

# RAG metrics
RAG_QUERY_COUNT = Counter(
    "rag_query_total",
    "Total number of RAG queries",
    ["workspace_id", "verdict"],
)

RAG_QUERY_LATENCY_SECONDS = Histogram(
    "rag_query_latency_seconds",
    "RAG query latency in seconds",
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10),
)

INGEST_JOB_COUNT = Counter(
    "ingest_job_total",
    "Total number of ingest jobs",
    ["workspace_id", "source"],
)

INGEST_JOB_LATENCY_SECONDS = Histogram(
    "ingest_job_latency_seconds",
    "Ingestion job latency in seconds",
    buckets=(0.5, 1, 2, 5, 10, 30, 60),
)

