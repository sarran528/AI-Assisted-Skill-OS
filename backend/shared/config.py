from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    api_base_url: str = "http://localhost:8000"
    database_url: str = "sqlite+aiosqlite:///./skillos.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "db+sqlite:///./celery_results.db"
    s3_bucket_name: str = "skillos-dev"
    s3_region: str = "us-east-1"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_endpoint_url: str | None = None
    jwt_private_key: str = ""
    jwt_public_key: str = ""
    jwt_kid: str = "local-1"
    jwt_access_ttl: int = 3600
    jwt_refresh_ttl: int = 2592000
    jwt_issuer: str = "https://skillos.app"
    jwt_audience: str = "skillos-api"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    serper_api_key: str = ""
    serpapi_api_key: str = ""
    search_provider: str = "serper"
    groq_api_key: str = ""
    together_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    together_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    llm_provider: str = "openai"
    llm_model: str = "claude-sonnet-4-20250514"
    llm_max_tokens: int = 1000
    llm_temperature: float = 0.0
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    embedding_batch_size: int = 100
    local_embedding_model: str = "all-MiniLM-L6-v2"
    faiss_index_path: str = "backend/data/faiss/skill_templates.index"
    faiss_metadata_path: str = "backend/data/faiss/skill_templates.meta.json"
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_storage_bucket: str = ""
    cors_allowed_origins: str = "http://localhost:3000"


settings = Settings()
