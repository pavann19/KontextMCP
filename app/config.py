import os
from pathlib import Path
from typing import List, Optional, Dict, Literal
from pydantic_settings import BaseSettings
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Secure Enterprise RAG & Agentic Knowledge Platform"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw"
    CORPUS_VARIANT: Literal["curated", "official"] = "curated"
    OFFICIAL_RAW_DATA_DIR: Path = BASE_DIR / "data" / "official"
    CHUNKS_DIR: Path = BASE_DIR / "data" / "chunks"
    QDRANT_STORAGE_DIR: Path = BASE_DIR / "data" / "qdrant_storage"
    AUDIT_LOG_PATH: Path = BASE_DIR / "data" / "audit_log.jsonl"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/enterprise_records.db"
    POSTGRES_URL: Optional[str] = "postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_rag"
    USE_SQLITE_FALLBACK: bool = True
    DATABASE_SCHEMA_MODE: Literal["create", "verify"] = "create"
    HTTP_MAX_BODY_BYTES: int = Field(default=1048576, ge=1024, le=16777216)
    HTTP_MAX_INFLIGHT: int = Field(default=16, ge=1, le=256)
    HTTP_BODY_TIMEOUT_SECONDS: float = Field(default=5, gt=0, le=60)
    HTTP_ALLOWED_HOSTS: List[str] = ["127.0.0.1", "localhost", "[::1]", "testserver"]
    
    # Qdrant Vector DB
    QDRANT_HOST: Optional[str] = None
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "eu_ai_act_bilingual"
    QDRANT_PREFER_LOCAL: bool = True  # Embedded local file storage
    
    # Retrieval Settings
    TOP_K_RETRIEVAL: int = 5
    HYBRID_ALPHA: float = 0.5  # Weight between Dense (alpha) and BM25 (1 - alpha)
    RRF_K: int = 60
    RERANKER_TOP_N: int = 3
    
    # Ollama Local Inference
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    SYNTHESIS_MODE: Literal["extractive", "ollama_select"] = "extractive"
    OLLAMA_MODEL: str = "qwen2.5:0.5b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    OLLAMA_REQUEST_TIMEOUT: float = 30.0
    
    # Langfuse Tracing
    LANGFUSE_PUBLIC_KEY: str = "pk-lf-local-dummy"
    LANGFUSE_SECRET_KEY: str = "sk-lf-local-dummy"
    LANGFUSE_HOST: str = "http://localhost:3000"
    LANGFUSE_ENABLED: bool = False  # Set to True if Langfuse server is running
    
    # Security & Guardrails
    ENABLE_PII_MASKING: bool = True
    ENABLE_PROMPT_GUARD: bool = True
    STRICT_TOOL_PERMISSIONS: bool = True
    API_KEYS: Dict[str, Dict[str, str]] = {}
    ALLOWED_ORIGINS: List[str] = []
    MCP_ALLOWED_HOSTS: List[str] = ["127.0.0.1", "localhost", "::1", "testserver"]
    AUDIT_CHECKPOINT_KEY: Optional[str] = None
    SECRET_KEY: Optional[str] = None

    def validate_runtime(self):
        """Fail before serving requests when production safeguards are incomplete."""
        if self.ENVIRONMENT != "production":
            return
        errors = []
        if self.DEBUG: errors.append("DEBUG must be false")
        if not all((self.ENABLE_PII_MASKING, self.ENABLE_PROMPT_GUARD, self.STRICT_TOOL_PERMISSIONS)):
            errors.append("guardrails must remain enabled")
        if not self.API_KEYS or any(len(key) < 32 for key in self.API_KEYS):
            errors.append("provision API credentials of at least 32 characters")
        from app.mcp.permissions import ROLE_CLEARANCE_MAP
        if any(identity.get("role") not in ROLE_CLEARANCE_MAP or not identity.get("username")
               or not identity.get("department") for identity in self.API_KEYS.values()):
            errors.append("configured identities must contain a known role, username and department")
        if not self.AUDIT_CHECKPOINT_KEY or len(self.AUDIT_CHECKPOINT_KEY) < 32:
            errors.append("provision an audit checkpoint key of at least 32 characters")
        if not self.DATABASE_URL.startswith(("postgresql://", "postgresql+psycopg2://")):
            errors.append("use PostgreSQL")
        else:
            from sqlalchemy.engine import make_url
            password = make_url(self.DATABASE_URL).password
            if not password or password in {"postgres", "password", "changeme"}:
                errors.append("provision a non-default database password")
        if self.DATABASE_SCHEMA_MODE != "verify": errors.append("migrate the schema and use verify mode")
        if self.QDRANT_PREFER_LOCAL or not self.QDRANT_HOST: errors.append("use remote Qdrant")
        if not self.HTTP_ALLOWED_HOSTS or any(host in {"*", "testserver"} or "*" in host for host in self.HTTP_ALLOWED_HOSTS):
            errors.append("configure explicit HTTP hosts")
        if "*" in self.ALLOWED_ORIGINS: errors.append("configure explicit browser origins")
        if errors:
            raise RuntimeError("Unsafe production configuration: " + "; ".join(errors))
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure necessary directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
settings.QDRANT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

