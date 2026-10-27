import os
from pathlib import Path
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Engineering Intelligence Hub"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.onrender.com",
        "*"
    ]

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    PORT: int = 8000

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CLONED_REPOS_DIR: Path = BASE_DIR / "cloned_repos"
    WORKSPACES_DIR: Path = BASE_DIR / "workspaces"
    CHROMA_PERSIST_DIR: Path = BASE_DIR / "chroma_db"

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'eih_data.db'}"
    SYNC_DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'eih_data.db'}"

    # LLM Settings
    LLM_PROVIDER: str = "mock" # mock | openai | groq | ollama | anthropic
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    ANTHROPIC_API_KEY: Optional[str] = None

    # Vector Store & Embeddings
    VECTOR_STORE: str = "chroma" # chroma | pgvector
    EMBEDDING_PROVIDER: str = "local" # local | sentence-transformers | openai
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Agent Settings
    MAX_AGENT_RETRIES: int = 3
    SANDBOX_TIMEOUT_SECONDS: int = 30
    ALLOW_SUBPROCESS_TESTS: bool = True

    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None

    model_config = {"env_file": ".env", "extra": "allow"}

settings = Settings()

# Ensure required runtime directories exist safely
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CLONED_REPOS_DIR.mkdir(parents=True, exist_ok=True)
settings.WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
