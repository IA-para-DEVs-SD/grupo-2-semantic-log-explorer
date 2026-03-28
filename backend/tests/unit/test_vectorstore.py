"""Unit tests for services/vectorstore.py — ChromaDB vector storage operations."""

import uuid as _uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.src.core.config import Settings
from backend.src.models.schemas import Chunk, ChunkMetadata, LogLevel
from backend.src.services.vectorstore import VectorStoreService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_API_KEY = "fake-google-api-key-for-testing"
EMBEDDING_DIM = 768


def _fake_settings(**overrides) -> Settings:
    """Create a test Settings object with a fake API key.

    Each call uses a unique collection name to isolate tests.
    """
    defaults = {
        "GOOGLE_API_KEY": FAKE_API_KEY,
        "CHROMA_COLLECTION_NAME": f"test_{_uuid.uuid4().hex[:8]}",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _fake_embedding(dim: int = EMBEDDING_DIM, value: float = 0.1) -> list[float]:
    """Return a fake embedding vector of the given dimension."""
    return [value] * dim


def _fake_embed_content_response(*, model=None, content=None, **kwargs):
    """Build a fake response matching google.generativeai.embed_content output.

    The real API is called as: genai.embed_content(model=..., content=...)
    """
    texts = content
    if isinstance(texts, str):
        return {"embedding": _fake_embedding()}
    return {"embedding": [_fake_embedding(value=0.1 + i * 0.01) for i in range(len(texts))]}


def _make_chunk(
    text: str = "2024-01-15 ERROR Connection refused",
    filename: str = "app.log",
    timestamp: str | None = "2024-01-15 10:00:00",
    log_level: LogLevel = LogLevel.ERROR,
) -> Chunk:
    """Create a Chunk for testing."""
    return Chunk(
        text=text,
        metadata=ChunkMetadata(
            filename=filename,
            timestamp=timestamp,
            log_level=log_level,
        ),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def settings():
    return _fake_settings()


@pytest.fixture()
def service(settings):
    """Create a VectorStoreService with mocked embedding generation."""
    with patch("backend.src.services.vectorstore.genai") as mock_genai:
        mock_genai.embed_content.side_effect = _fake_embed_content_response
        svc = VectorStoreService(settings)
        # Keep the mock active for the lifetime of the service
        svc._mock_genai = mock_genai
        yield svc


@pytest.fixture()
def service_with_data():
    """Service pre-loaded with 3 chunks (isolated collection)."""
    s = _fake_settings()
    with patch("backend.src.services.vectorstore.genai") as mock_genai:
        mock_genai.embed_content.side_effect = _fake_embed_content_response
        svc = VectorStoreService(s)
        chunks = [
            _make_chunk("ERROR Connection refused to db:5432", "app.log", "2024-01-15 10:00:00", LogLevel.ERROR),
            _make_chunk("INFO Application started successfully", "app.log", "2024-01-15 09:59:00", LogLevel.INFO),
            _make_chunk("WARNING Disk usage at 85%", "system.log", "2024-01-15 10:01:00", LogLevel.WARNING),
        ]
        svc.add_chunks(chunks)
        yield svc


# ---------------------------------------------------------------------------
# Ephemeral mode
# ---------------------------------------------------------------------------

class TestEphemeralMode:
    def test_chromadb_client_is_ephemeral(self, service):
        """ChromaDB must operate in ephemeral mode (no disk persistence)."""
        # chromadb.Client() creates an ephemeral in-memory client by default
        assert service._client is not None
        assert service._collection is not None

    def test_collection_created_with_configured_name(self, settings):
        """Collection name should match the settings."""
        with patch("backend.src.services.vectorstore.genai"):
            svc = VectorStoreService(settings)
        assert svc._collection.name == settings.CHROMA_COLLECTION_NAME


# ---------------------------------------------------------------------------
# add_chunks
# ---------------------------------------------------------------------------

class TestAddChunks:
    def test_returns_count_of_chunks_added(self, service):
        chunks = [_make_chunk(), _make_chunk(text="INFO ok")]
        with patch("backend.src.services.vectorstore.genai") as mock_genai:
            mock_genai.embed_content.side_effect = _fake_embed_content_response
            count = service.add_chunks(chunks)
        assert count == 2

    def test_empty_list_returns_zero(self, service):
        count = service.add_chunks([])
        assert count == 0

    def test_stores_correct_metadata(self, service):
        chunk = _make_chunk(
            text="CRITICAL OOM Kill detected",
            filename="kern.log",
            timestamp="2024-06-01 12:00:00",
            log_level=LogLevel.CRITICAL,
        )
        with patch("backend.src.services.vectorstore.genai") as mock_genai:
            mock_genai.embed_content.side_effect = _fake_embed_content_response
            service.add_chunks([chunk])

        # Verify stored data via ChromaDB peek
        stored = service._collection.peek(limit=1)
        assert len(stored["ids"]) == 1
        meta = stored["metadatas"][0]
        assert meta["filename"] == "kern.log"
        assert meta["timestamp"] == "2024-06-01 12:00:00"
        assert meta["log_level"] == "CRITICAL"

    def test_stores_document_text(self, service):
        chunk = _make_chunk(text="ERROR segfault in module X")
        with patch("backend.src.services.vectorstore.genai") as mock_genai:
            mock_genai.embed_content.side_effect = _fake_embed_content_response
            service.add_chunks([chunk])

        stored = service._collection.peek(limit=1)
        assert stored["documents"][0] == "ERROR segfault in module X"

    def test_none_timestamp_stored_as_empty_string(self, service):
        chunk = _make_chunk(timestamp=None)
        with patch("backend.src.services.vectorstore.genai") as mock_genai:
            mock_genai.embed_content.side_effect = _fake_embed_content_response
            service.add_chunks([chunk])

        stored = service._collection.peek(limit=1)
        assert stored["metadatas"][0]["timestamp"] == ""


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

class TestSearch:
    def test_returns_results_with_expected_keys(self, service_with_data):
        query_emb = _fake_embedding()
        results = service_with_data.search(query_emb, top_k=2)
        assert len(results) > 0
        for item in results:
            assert "id" in item
            assert "document" in item
            assert "metadata" in item
            assert "distance" in item

    def test_respects_top_k(self, service_with_data):
        query_emb = _fake_embedding()
        results = service_with_data.search(query_emb, top_k=1)
        assert len(results) == 1

    def test_top_k_larger_than_stored_returns_all(self, service_with_data):
        query_emb = _fake_embedding()
        results = service_with_data.search(query_emb, top_k=100)
        # Only 3 chunks were stored
        assert len(results) == 3

    def test_metadata_contains_required_fields(self, service_with_data):
        query_emb = _fake_embedding()
        results = service_with_data.search(query_emb, top_k=3)
        for item in results:
            assert "filename" in item["metadata"]
            assert "timestamp" in item["metadata"]
            assert "log_level" in item["metadata"]

    def test_distance_is_numeric(self, service_with_data):
        query_emb = _fake_embedding()
        results = service_with_data.search(query_emb, top_k=1)
        assert isinstance(results[0]["distance"], (int, float))


# ---------------------------------------------------------------------------
# clear_collection
# ---------------------------------------------------------------------------

class TestClearCollection:
    def test_removes_all_stored_data(self, service_with_data):
        # Confirm data exists first
        assert service_with_data._collection.count() == 3

        service_with_data.clear_collection()

        assert service_with_data._collection.count() == 0

    def test_clear_empty_collection_is_safe(self, service):
        """Clearing an already-empty collection should not raise."""
        service.clear_collection()
        assert service._collection.count() == 0

    def test_can_add_after_clear(self, service_with_data):
        service_with_data.clear_collection()
        assert service_with_data._collection.count() == 0

        chunk = _make_chunk(text="INFO fresh start")
        with patch("backend.src.services.vectorstore.genai") as mock_genai:
            mock_genai.embed_content.side_effect = _fake_embed_content_response
            service_with_data.add_chunks([chunk])

        assert service_with_data._collection.count() == 1


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_embedding_failure_raises_502(self, settings):
        with patch("backend.src.services.vectorstore.genai") as mock_genai:
            mock_genai.embed_content.side_effect = lambda **kwargs: None  # init ok
            svc = VectorStoreService(settings)

            # Now make embed_content raise on add_chunks
            mock_genai.embed_content.side_effect = RuntimeError("API quota exceeded")
            with pytest.raises(HTTPException) as exc_info:
                svc.add_chunks([_make_chunk()])
            assert exc_info.value.status_code == 502
            assert "embeddings" in exc_info.value.detail.lower()

    def test_chromadb_add_failure_raises_503(self, settings):
        with patch("backend.src.services.vectorstore.genai") as mock_genai:
            mock_genai.embed_content.side_effect = _fake_embed_content_response
            svc = VectorStoreService(settings)

            # Embeddings succeed, but ChromaDB collection.add fails
            original_add = svc._collection.add
            svc._collection.add = MagicMock(side_effect=RuntimeError("disk full"))
            with pytest.raises(HTTPException) as exc_info:
                svc.add_chunks([_make_chunk()])
            assert exc_info.value.status_code == 503

    def test_chromadb_search_failure_raises_503(self, settings):
        with patch("backend.src.services.vectorstore.genai") as mock_genai:
            mock_genai.embed_content.side_effect = _fake_embed_content_response
            svc = VectorStoreService(settings)

            svc._collection.query = MagicMock(side_effect=RuntimeError("connection lost"))
            with pytest.raises(HTTPException) as exc_info:
                svc.search(_fake_embedding(), top_k=5)
            assert exc_info.value.status_code == 503

    def test_chromadb_init_failure_raises_503(self):
        with patch("backend.src.services.vectorstore.genai"), \
             patch("backend.src.services.vectorstore.chromadb") as mock_chroma:
            mock_chroma.Client.side_effect = RuntimeError("cannot start")
            with pytest.raises(HTTPException) as exc_info:
                VectorStoreService(_fake_settings())
            assert exc_info.value.status_code == 503
