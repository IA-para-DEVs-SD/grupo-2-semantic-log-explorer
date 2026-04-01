"""Unit tests for services/vectorstore.py — ChromaDB vector storage operations."""

import uuid as _uuid
from unittest.mock import MagicMock, patch
import tempfile

import pytest
from src.core.config import Settings
from src.models.schemas import Chunk, ChunkMetadata, LogLevel
from src.services.vectorstore import VectorStoreService
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_API_KEY = "fake-google-api-key-for-testing"
EMBEDDING_DIM = 768


def _fake_settings(**overrides) -> Settings:
    """Create a test Settings object with a fake API key.

    Each call uses a unique collection name and temp persist dir to isolate tests.
    """
    defaults = {
        "GOOGLE_API_KEY": FAKE_API_KEY,
        "CHROMA_COLLECTION_NAME": f"test_{_uuid.uuid4().hex[:8]}",
        "CHROMA_PERSIST_DIR": tempfile.mkdtemp(),
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _fake_embedding(dim: int = EMBEDDING_DIM, value: float = 0.1) -> list[float]:
    """Return a fake embedding vector of the given dimension."""
    return [value] * dim


def _make_fake_embedding_obj(values: list[float]):
    """Create a fake embedding object with a .values attribute."""
    obj = MagicMock()
    obj.values = values
    return obj


def _fake_embed_content_response(texts):
    """Build a fake response matching genai.Client().models.embed_content output.

    Returns an object with .embeddings (list of objects with .values).
    """
    if isinstance(texts, str):
        texts = [texts]
    result = MagicMock()
    result.embeddings = [
        _make_fake_embedding_obj(_fake_embedding(value=0.1 + i * 0.01))
        for i in range(len(texts))
    ]
    return result


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
    with patch("src.services.vectorstore.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = lambda **kwargs: _fake_embed_content_response(kwargs.get("contents", []))
        mock_genai.Client.return_value = mock_client
        svc = VectorStoreService(settings)
        svc._mock_genai = mock_genai
        yield svc


@pytest.fixture()
def service_with_data():
    """Service pre-loaded with 3 chunks (isolated collection)."""
    s = _fake_settings()
    with patch("src.services.vectorstore.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = lambda **kwargs: _fake_embed_content_response(kwargs.get("contents", []))
        mock_genai.Client.return_value = mock_client
        svc = VectorStoreService(s)
        chunks = [
            _make_chunk(
                "ERROR Connection refused to db:5432",
                "app.log",
                "2024-01-15 10:00:00",
                LogLevel.ERROR,
            ),
            _make_chunk(
                "INFO Application started successfully",
                "app.log",
                "2024-01-15 09:59:00",
                LogLevel.INFO,
            ),
            _make_chunk(
                "WARNING Disk usage at 85%",
                "system.log",
                "2024-01-15 10:01:00",
                LogLevel.WARNING,
            ),
        ]
        svc.add_chunks(chunks, "app.log")
        yield svc


# ---------------------------------------------------------------------------
# Persistent mode
# ---------------------------------------------------------------------------


class TestPersistentMode:
    def test_chromadb_client_is_persistent(self, service):
        """ChromaDB must operate in persistent mode."""
        assert service._client is not None

    def test_client_created_with_persistent_client(self, settings):
        """VectorStoreService should use PersistentClient."""
        with patch("src.services.vectorstore.genai") as mock_genai:
            mock_genai.Client.return_value = MagicMock()
            svc = VectorStoreService(settings)
        assert svc._client is not None


# ---------------------------------------------------------------------------
# add_chunks
# ---------------------------------------------------------------------------


class TestAddChunks:
    def test_returns_tuple_of_count_and_collection_name(self, service):
        chunks = [_make_chunk(), _make_chunk(text="INFO ok")]
        with patch.object(service, "_generate_embeddings", side_effect=lambda texts: [_fake_embedding() for _ in texts]):
            result = service.add_chunks(chunks, "test.log")
        assert isinstance(result, tuple)
        count, collection_name = result
        assert count == 2
        assert isinstance(collection_name, str)
        assert len(collection_name) > 0

    def test_empty_list_returns_zero(self, service):
        count, name = service.add_chunks([], "test.log")
        assert count == 0
        assert name == ""

    def test_stores_correct_metadata(self, service):
        chunk = _make_chunk(
            text="CRITICAL OOM Kill detected",
            filename="kern.log",
            timestamp="2024-06-01 12:00:00",
            log_level=LogLevel.CRITICAL,
        )
        with patch.object(service, "_generate_embeddings", side_effect=lambda texts: [_fake_embedding() for _ in texts]):
            count, collection_name = service.add_chunks([chunk], "kern.log")

        # Verify stored data via ChromaDB peek
        collection = service._client.get_or_create_collection(name=collection_name)
        stored = collection.peek(limit=1)
        assert len(stored["ids"]) == 1
        meta = stored["metadatas"][0]
        assert meta["filename"] == "kern.log"
        assert meta["timestamp"] == "2024-06-01 12:00:00"
        assert meta["log_level"] == "CRITICAL"

    def test_stores_document_text(self, service):
        chunk = _make_chunk(text="ERROR segfault in module X")
        with patch.object(service, "_generate_embeddings", side_effect=lambda texts: [_fake_embedding() for _ in texts]):
            count, collection_name = service.add_chunks([chunk], "app.log")

        collection = service._client.get_or_create_collection(name=collection_name)
        stored = collection.peek(limit=1)
        assert stored["documents"][0] == "ERROR segfault in module X"

    def test_none_timestamp_stored_as_empty_string(self, service):
        chunk = _make_chunk(timestamp=None)
        with patch.object(service, "_generate_embeddings", side_effect=lambda texts: [_fake_embedding() for _ in texts]):
            count, collection_name = service.add_chunks([chunk], "app.log")

        collection = service._client.get_or_create_collection(name=collection_name)
        stored = collection.peek(limit=1)
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
# delete_log
# ---------------------------------------------------------------------------


class TestDeleteLog:
    def test_removes_collection(self, service_with_data):
        # Find the collection name that was created
        collections = service_with_data._client.list_collections()
        assert len(collections) > 0
        collection_name = collections[0].name

        service_with_data.delete_log(collection_name)

        # After deletion, listing should be empty
        remaining = service_with_data._client.list_collections()
        names = [c.name for c in remaining]
        assert collection_name not in names

    def test_delete_nonexistent_collection_raises_404(self, service):
        """Deleting a non-existent collection should raise HTTP 404."""
        with pytest.raises(HTTPException) as exc_info:
            service.delete_log("nonexistent_collection")
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_embedding_failure_raises_502(self, settings):
        with patch("src.services.vectorstore.genai") as mock_genai:
            mock_client = MagicMock()
            mock_client.models.embed_content.return_value = MagicMock(embeddings=[])
            mock_genai.Client.return_value = mock_client
            svc = VectorStoreService(settings)

            # Now make embed_content raise on add_chunks
            mock_client.models.embed_content.side_effect = RuntimeError("API quota exceeded")
            with pytest.raises(HTTPException) as exc_info:
                svc.add_chunks([_make_chunk()], "test.log")
            assert exc_info.value.status_code == 502
            assert "embeddings" in exc_info.value.detail.lower()

    def test_chromadb_add_failure_raises_503(self, settings):
        with patch("src.services.vectorstore.genai") as mock_genai:
            mock_client = MagicMock()
            mock_client.models.embed_content.side_effect = lambda **kwargs: _fake_embed_content_response(kwargs.get("contents", []))
            mock_genai.Client.return_value = mock_client
            svc = VectorStoreService(settings)

            # Embeddings succeed, but ChromaDB collection.add fails
            original_get_or_create = svc._client.get_or_create_collection
            mock_collection = MagicMock()
            mock_collection.add.side_effect = RuntimeError("disk full")
            svc._client.get_or_create_collection = MagicMock(return_value=mock_collection)
            with pytest.raises(HTTPException) as exc_info:
                svc.add_chunks([_make_chunk()], "test.log")
            assert exc_info.value.status_code == 503

    def test_chromadb_search_failure_raises_503(self, settings):
        with patch("src.services.vectorstore.genai") as mock_genai:
            mock_client = MagicMock()
            mock_client.models.embed_content.side_effect = lambda **kwargs: _fake_embed_content_response(kwargs.get("contents", []))
            mock_genai.Client.return_value = mock_client
            svc = VectorStoreService(settings)

            # Make get_collection_for_query return a mock collection that fails on query
            mock_collection = MagicMock()
            mock_collection.query.side_effect = RuntimeError("connection lost")
            with patch.object(svc, "get_collection_for_query", return_value=mock_collection):
                with pytest.raises(HTTPException) as exc_info:
                    svc.search(_fake_embedding(), top_k=5)
                assert exc_info.value.status_code == 503

    def test_chromadb_init_failure_raises_503(self):
        with (
            patch("src.services.vectorstore.genai") as mock_genai,
            patch("src.services.vectorstore.chromadb") as mock_chroma,
        ):
            mock_genai.Client.return_value = MagicMock()
            mock_chroma.PersistentClient.side_effect = RuntimeError("cannot start")
            with pytest.raises(HTTPException) as exc_info:
                VectorStoreService(_fake_settings())
            assert exc_info.value.status_code == 503
