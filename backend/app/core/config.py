from typing import List, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SignalOS"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & Auth
    SECRET_KEY: str = "signalos-super-secret-production-jwt-key-2026-secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database & pgvector
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "signalos"
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str) and v:
            return v
        data = info.data
        return (
            f"postgresql+asyncpg://{data.get('POSTGRES_USER', 'postgres')}:"
            f"{data.get('POSTGRES_PASSWORD', 'postgres')}@"
            f"{data.get('POSTGRES_SERVER', 'localhost')}:"
            f"{data.get('POSTGRES_PORT', 5432)}/"
            f"{data.get('POSTGRES_DB', 'signalos')}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None

    @field_validator("REDIS_URL", mode="before")
    def assemble_redis_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str) and v:
            return v
        data = info.data
        pwd = f":{data.get('REDIS_PASSWORD')}@" if data.get("REDIS_PASSWORD") else ""
        return f"redis://{pwd}{data.get('REDIS_HOST', 'localhost')}:{data.get('REDIS_PORT', 6379)}/0"

    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_FAST_MODEL: str = "gpt-4o-mini"
    DEFAULT_REASONING_MODEL: str = "gpt-4o"

    # Agent Loop Guardrails
    MAX_AGENT_STEPS: int = 15
    MAX_TOOL_CALLS: int = 30
    MAX_RUNTIME_SECONDS: int = 180
    MAX_COST_USD: float = 0.50

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE_USER: int = 100
    RATE_LIMIT_PER_MINUTE_ORG: int = 1000

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
