"""Root conftest — shared fixtures and Hypothesis profile configuration.

Provides reusable fixtures for all test modules (unit and property) and
registers Hypothesis profiles for consistent property-based testing.
"""

import os
from unittest.mock import MagicMock

import pytest
from src.api.dependencies import (
    get_llm_service,
    get_settings_dep,
    get_vectorstore_service,
)
from src.api.routes.chat import router as chat_router
from src.api.routes.upload import router as upload_router
from src.core.config import Settings
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from hypothesis import HealthCheck
from hypothesis import settings as hypothesis_settings

# ---------------------------------------------------------------------------
# Hypothesis profiles
# ---------------------------------------------------------------------------

hypothesis_settings.register_profile("default", max_examples=200)
hypothesis_settings.register_profile(
    "ci",
    max_examples=500,
    suppress_health_check=[HealthCheck.too_slow],
)
hypothesis_settings.register_profile("dev", max_examples=10)

if os.environ.get("CI"):
    hypothesis_settings.load_profile("ci")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_settings() -> Settings:
    """Return a valid ``Settings`` instance with test defaults."""
    return Settings(
        GOOGLE_API_KEY="test-key",
        CHROMA_COLLECTION_NAME="test_collection",
        MAX_FILE_SIZE_MB=50,
        ALLOWED_EXTENSIONS={".log", ".txt", ".json"},
    )


@pytest.fixture
def mock_vectorstore() -> MagicMock:
    """Return a mock ``VectorStoreService``."""
    mock = MagicMock()
    mock.add_chunks.return_value = 3
    mock._collection = MagicMock()
    mock._collection.count.return_value = 5
    return mock


@pytest.fixture
def mock_llm_service() -> MagicMock:
    """Return a mock ``LLMService`` with an async streaming helper."""
    mock = MagicMock()

    async def mock_stream(*args, **kwargs):
        yield "Test response"
        yield " from LLM"

    mock.generate_stream = mock_stream
    return mock


@pytest.fixture
def test_app(
    mock_settings: Settings,
    mock_vectorstore: MagicMock,
    mock_llm_service: MagicMock,
) -> FastAPI:
    """Return a ``FastAPI`` app with upload/chat routes and mocked deps."""
    app = FastAPI()
    app.include_router(upload_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")

    app.dependency_overrides[get_settings_dep] = lambda: mock_settings
    app.dependency_overrides[get_vectorstore_service] = lambda: mock_vectorstore
    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service

    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Return a synchronous ``TestClient`` bound to *test_app*."""
    return TestClient(test_app)


@pytest.fixture
async def async_client(test_app: FastAPI):
    """Yield an async ``httpx.AsyncClient`` bound to *test_app*."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
