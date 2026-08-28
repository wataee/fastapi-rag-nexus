import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI RAG Nexus Engine"
    VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Server & Security
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "nexus-super-secret-jwt-key-2026-production-ready"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    CORS_ORIGINS: List[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # PostgreSQL & PGVector
    DB_HOST: str = Field(default="localhost", alias="DB_HOST")
    DB_PORT: int = Field(default=5432, alias="DB_PORT")
    DB_USER: str = Field(default="postgres", alias="DB_USER")
    DB_PASS: str = Field(default="postgres", alias="DB_PASS")
    DB_NAME: str = Field(default="nexus_rag_db", alias="DB_NAME")
    COLLECTION_NAME: str = "nexus_knowledge_docs"

    # Redis
    REDIS_HOST: str = Field(default="localhost", alias="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, alias="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    SESSION_TTL_SECONDS: int = 86400

    # OpenAI & LLM Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    OPENAI_API_BASE: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Retrieval
    RETRIEVAL_TOP_K: int = 4
    SIMILARITY_SCORE_THRESHOLD: float = 0.35

    @property
    def sync_database_uri(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
