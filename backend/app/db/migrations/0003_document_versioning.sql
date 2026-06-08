-- Document versioning + versioned ingestion jobs

CREATE TABLE IF NOT EXISTS document_versions (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id),
  version_number INTEGER NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'active',
  content_fingerprint VARCHAR(128),
  s3_key VARCHAR(1024) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(document_id, version_number)
);

CREATE TABLE IF NOT EXISTS ingest_jobs (
  id SERIAL PRIMARY KEY,
  workspace_id INTEGER NOT NULL REFERENCES workspaces(id),
  document_id INTEGER NOT NULL REFERENCES documents(id),
  version_id INTEGER NOT NULL REFERENCES document_versions(id),
  status VARCHAR(50) NOT NULL DEFAULT 'queued',
  records INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

