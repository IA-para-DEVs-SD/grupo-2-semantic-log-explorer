from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    GOOGLE_API_KEY: str
    CHROMA_COLLECTION_NAME: str = "log_chunks"
    CHROMA_PERSIST_DIR: str = ".chromadb"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: set[str] = {".log", ".txt", ".json"}
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:80"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return {ext.strip() for ext in v.split(",") if ext.strip()}
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("GOOGLE_API_KEY")
    @classmethod
    def google_api_key_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(
                "GOOGLE_API_KEY is required but was not set or is empty. "
                "Please define it in your .env file or environment variables."
            )
        return v.strip()


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance. Fails fast if GOOGLE_API_KEY is missing."""
    return Settings()  # type: ignore[call-arg]
