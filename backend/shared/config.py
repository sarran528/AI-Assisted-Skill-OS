from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "local"
    api_base_url: str = "http://localhost:8000"
    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str
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
    llm_provider: str = "openai"
    llm_model: str = "claude-sonnet-4-20250514"
    llm_max_tokens: int = 1000
    llm_temperature: float = 0.0
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    nhost_storage_endpoint: str = ""
    nhost_storage_bucket: str = ""
    nhost_storage_access_key: str = ""
    nhost_storage_secret_key: str = ""
    cors_allowed_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"


settings = Settings()
