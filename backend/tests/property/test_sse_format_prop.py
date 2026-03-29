"""Property-based test for SSE format in chat responses.

Feature: semantic-log-explorer, Property 9: Resposta de chat utiliza formato SSE

For any response from the POST /api/chat endpoint, the content-type must be
`text/event-stream` and the data must follow SSE format (prefix `data:` in each event).

Validates: Requirement 9.1
"""

from unittest.mock import patch, MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.src.api.routes.chat import router as chat_router
from backend.src.core.config import Settings
from backend.src.models.schemas import Chunk, ChunkMetadata, LogLevel


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_EXTENSIONS = {".log", ".txt", ".json"}


# ---------------------------------------------------------------------------
# Strategies — generators for chat questions and tokens
# ---------------------------------------------------------------------------

# Strategy for valid questions (1-2000 chars as per ChatRequest schema)
_question_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S", "Z"),
        blacklist_characters="\x00",
    ),
    min_size=1,
    max_size=2000,
).filter(lambda x: len(x.strip()) > 0)

# Strategy for random tokens yielded by LLM
_token_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S", "Z"),
        blacklist_characters="\x00\n",
    ),
    min_size=1,
    max_size=50,
)

# Strategy for number of tokens in response
_token_count_strategy = st.integers(min_value=1, max_value=10)


# ---------------------------------------------------------------------------
# Fixtures (inline for property tests)
# ---------------------------------------------------------------------------

def create_test_app(mock_vectorstore, mock_llm_service):
    """Create FastAPI app with mocked dependencies for testing."""
    from backend.src.api.dependencies import (
        get_settings_dep,
        get_vectorstore_service,
        get_llm_service,
    )

    mock_settings = Settings(
        GOOGLE_API_KEY="test-api-key",
        CHROMA_COLLECTION_NAME="test_collection",
        MAX_FILE_SIZE_MB=50,
        ALLOWED_EXTENSIONS=VALID_EXTENSIONS,
    )

    test_app = FastAPI()
    test_app.include_router(chat_router, prefix="/api")

    test_app.dependency_overrides[get_settings_dep] = lambda: mock_settings
    test_app.dependency_overrides[get_vectorstore_service] = lambda: mock_vectorstore
    test_app.dependency_overrides[get_llm_service] = lambda: mock_llm_service

    return test_app


def create_mock_vectorstore():
    """Create mock VectorStoreService with non-empty collection."""
    mock = MagicMock()
    mock._collection = MagicMock()
    mock._collection.count.return_value = 5  # Non-empty collection
    return mock


def create_mock_llm_service(tokens: list[str]):
    """Create mock LLMService that yields the given tokens."""
    mock = MagicMock()

    async def mock_stream(*args, **kwargs):
        for token in tokens:
            yield token

    mock.generate_stream = mock_stream
    return mock


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    question=_question_strategy,
    tokens=st.lists(_token_strategy, min_size=1, max_size=10),
)
def test_chat_response_uses_sse_format(
    question: str,
    tokens: list[str],
) -> None:
    """Property 9: Chat response uses SSE format.
    
    For any response from POST /api/chat:
    - Content-Type must be `text/event-stream`
    - Data must follow SSE format (prefix `data:` in each event)
    """
    mock_vectorstore = create_mock_vectorstore()
    mock_llm_service = create_mock_llm_service(tokens)

    app = create_test_app(mock_vectorstore, mock_llm_service)
    client = TestClient(app)

    # Mock retrieve to return some chunks
    mock_chunks = [
        Chunk(
            text="2024-01-15 10:00:00 INFO Test log entry",
            metadata=ChunkMetadata(filename="test.log", log_level=LogLevel.INFO),
        ),
    ]

    with patch("backend.src.api.routes.chat.retrieve") as mock_retrieve:
        mock_retrieve.return_value = mock_chunks

        response = client.post("/api/chat", json={"question": question})

        # Property 9.1: Response must be successful
        assert response.status_code == 200, (
            f"Expected HTTP 200, got {response.status_code}: {response.text}"
        )

        # Property 9.2: Content-Type must be text/event-stream
        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type, (
            f"Expected Content-Type to contain 'text/event-stream', "
            f"got '{content_type}'"
        )

        # Property 9.3: Response data must follow SSE format
        content = response.text

        # SSE format requires each event to have "data:" prefix
        # The response should contain at least one "data:" prefix
        assert "data:" in content, (
            f"Expected SSE format with 'data:' prefix, got: {content!r}"
        )

        # Verify each non-empty line that is an event has the data: prefix
        lines = content.split("\n")
        data_lines = [line for line in lines if line.strip() and not line.startswith(":")]
        
        for line in data_lines:
            assert line.startswith("data:"), (
                f"Expected SSE event line to start with 'data:', got: {line!r}"
            )

        # Verify that all tokens appear in the response
        for token in tokens:
            assert token in content, (
                f"Expected token {token!r} to appear in SSE response"
            )
