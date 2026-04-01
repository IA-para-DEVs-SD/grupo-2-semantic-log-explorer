"""Unit tests for services/retriever.py — semantic search retrieval."""

import uuid as _uuid
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from src.core.config import Settings
from src.models.schemas import Chunk, ChunkMetadata, LogLevel
from src.services.retriever import retrieve
from src.services.vectorstore import VectorStoreService

# ---------------------------------------------------------------------------
# Constants & Helpers
# ---------------------------------------------------------------------------

FAKE_API_KEY = "fake-google-api-key-for-testing"
EMBEDDING_DIM = 768


def _fake_settings(**overrides) -> Settings:
    defaults = {
        "GOOGLE_API_KEY": FAKE_API_KEY,
        "CHROMA_COLLECTION_NAME": f"test_{_uuid.uuid4().hex[:8]}",
        "CHROMA_PERSIST_DIR": tempfile.mkdtemp(),
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _fake_embedding(dim: int = EMBEDDING_DIM, value: float = 0.1) -> list[float]:
    return [value] * dim


def _make_fake_embedding_obj(values: list[float]):
    obj = MagicMock()
    obj.values = values
    return obj


def _fake_embed_content_response(texts):
    """Build a fake response matching genai.Client().models.embed_content output."""
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
def service_with_data():
    """VectorStoreService pre-loaded with 3 chunks."""
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


@pytest.fixture()
def empty_service():
    """VectorStoreService with no indexed data."""
    s = _fake_settings()
    with patch("src.services.vectorstore.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = lambda **kwargs: _fake_embed_content_response(kwargs.get("contents", []))
        mock_genai.Client.return_value = mock_client
        svc = VectorStoreService(s)
        yield svc


# ---------------------------------------------------------------------------
# Basic retrieval
# ---------------------------------------------------------------------------


class TestRetrieve:
    def test_returns_list_of_chunks(self, service_with_data):
        results = retrieve("connection error", service_with_data, top_k=3)
        assert isinstance(results, list)
        assert all(isinstance(c, Chunk) for c in results)

    def test_returns_chunks_with_valid_metadata(self, service_with_data):
        results = retrieve("connection error", service_with_data, top_k=3)
        for chunk in results:
            assert chunk.metadata.filename != ""
            assert isinstance(chunk.metadata.log_level, LogLevel)

    def test_respects_top_k(self, service_with_data):
        results = retrieve("error", service_with_data, top_k=1)
        assert len(results) == 1

    def test_top_k_larger_than_stored_returns_all(self, service_with_data):
        results = retrieve("error", service_with_data, top_k=10)
        assert len(results) == 3

    def test_empty_collection_returns_empty_list(self, empty_service):
        results = retrieve("anything", empty_service, top_k=5)
        assert results == []


# ---------------------------------------------------------------------------
# top_k clamping
# ---------------------------------------------------------------------------


class TestTopKClamping:
    def test_top_k_below_one_clamped_to_one(self, service_with_data):
        results = retrieve("error", service_with_data, top_k=0)
        assert len(results) >= 1

    def test_top_k_above_ten_clamped_to_ten(self, service_with_data):
        results = retrieve("error", service_with_data, top_k=50)
        # Only 3 stored, but top_k should have been clamped to 10
        assert len(results) <= 10

    def test_negative_top_k_clamped_to_one(self, service_with_data):
        results = retrieve("error", service_with_data, top_k=-5)
        assert len(results) >= 1


# ---------------------------------------------------------------------------
# Metadata reconstruction
# ---------------------------------------------------------------------------


class TestMetadataReconstruction:
    def test_log_level_reconstructed_correctly(self, service_with_data):
        results = retrieve("error", service_with_data, top_k=3)
        levels = {c.metadata.log_level for c in results}
        assert levels.issubset(set(LogLevel))

    def test_empty_timestamp_becomes_none(self):
        """When ChromaDB stores '' for timestamp, retriever should return None."""
        s = _fake_settings()
        with patch("src.services.vectorstore.genai") as mock_genai:
            mock_client = MagicMock()
            mock_client.models.embed_content.side_effect = lambda **kwargs: _fake_embed_content_response(kwargs.get("contents", []))
            mock_genai.Client.return_value = mock_client
            svc = VectorStoreService(s)
            svc.add_chunks([_make_chunk(timestamp=None)], "app.log")
            results = retrieve("error", svc, top_k=1)
        assert results[0].metadata.timestamp is None

    def test_invalid_log_level_defaults_to_unknown(self):
        """If ChromaDB metadata has an unrecognised log_level, default to UNKNOWN."""
        s = _fake_settings()
        with patch("src.services.vectorstore.genai") as mock_genai:
            mock_client = MagicMock()
            mock_client.models.embed_content.side_effect = lambda **kwargs: _fake_embed_content_response(kwargs.get("contents", []))
            mock_genai.Client.return_value = mock_client
            svc = VectorStoreService(s)
            _count, collection_name = svc.add_chunks([_make_chunk()], "app.log")

            # Manually corrupt the stored metadata
            collection = svc._client.get_or_create_collection(name=collection_name)
            stored = collection.get(include=["metadatas"])
            doc_id = stored["ids"][0]
            collection.update(
                ids=[doc_id],
                metadatas=[
                    {
                        "filename": "app.log",
                        "timestamp": "",
                        "log_level": "INVALID_LEVEL",
                    }
                ],
            )

            results = retrieve("error", svc, top_k=1)
        assert results[0].metadata.log_level == LogLevel.UNKNOWN
