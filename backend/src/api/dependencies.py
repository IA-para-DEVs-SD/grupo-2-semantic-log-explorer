"""Dependency injection providers for FastAPI routes."""

from functools import lru_cache

from src.core.config import Settings, get_settings


def get_settings_dep() -> Settings:
    """Provide the application Settings instance."""
    return get_settings()


@lru_cache
def _get_vectorstore_service():
    """Create and cache a singleton VectorStoreService."""
    from src.services.vectorstore import VectorStoreService

    settings = get_settings()
    return VectorStoreService(settings=settings)


@lru_cache
def _get_llm_service():
    """Create and cache a singleton LLMService."""
    from src.services.llm import LLMService

    settings = get_settings()
    return LLMService(settings=settings)


def get_vectorstore_service():
    """Provide the VectorStoreService instance."""
    return _get_vectorstore_service()


def get_llm_service():
    """Provide the LLMService instance."""
    return _get_llm_service()
