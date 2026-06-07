from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Server
    app_name: str = "Enterprise Knowledge Copilot"
    version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8000

    # JWT/Auth (placeholder defaults)
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_exp_seconds: int = 60 * 60 * 24 * 7

    # Multi-tenant / RBAC
    default_workspace_role: str = "viewer"

    # Vector DB
    vector_db_url: str = "http://localhost:6333"  # Qdrant-like; overridden per deployment
    pgvector_dsn: str = "postgresql://postgres:postgres@localhost:5432/ekc"

    # Embeddings / LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # S3
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""

    # Observability
    otel_service_name: str = "enterprise-knowledge-copilot"
    prometheus_path: str = "/metrics"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

