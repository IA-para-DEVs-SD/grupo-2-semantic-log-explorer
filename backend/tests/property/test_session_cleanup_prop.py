"""Property-based test for session cleanup — deleting a log removes all its data.

Feature: semantic-log-explorer, Property 8: Limpeza de sessão remove todos os dados

Para qualquer coleção no ChromaDB com dados armazenados, após a execução da
limpeza de sessão (delete_log), a coleção deve ser removida.

**Validates: Requirement 8.3**
"""

import uuid as _uuid
import tempfile
from unittest.mock import MagicMock, patch

from src.core.config import Settings
from src.models.schemas import Chunk, ChunkMetadata, LogLevel
from src.services.vectorstore import VectorStoreService
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EMBEDDING_DIM = 768
FAKE_API_KEY = "fake-google-api-key-for-testing"

# ---------------------------------------------------------------------------
# Strategies — generators for random chunks
# ---------------------------------------------------------------------------

_chunk_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=200,
)

_filename = st.builds(
    lambda name, ext: f"{name}{ext}",
    name=st.from_regex(r"[a-zA-Z0-9_]{1,20}", fullmatch=True),
    ext=st.sampled_from([".log", ".txt", ".json"]),
)

_timestamp = st.one_of(
    st.none(),
    st.builds(
        lambda y, mo, d, h, mi, s: f"{y:04d}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}",
        y=st.integers(min_value=2020, max_value=2025),
        mo=st.integers(min_value=1, max_value=12),
        d=st.integers(min_value=1, max_value=28),
        h=st.integers(min_value=0, max_value=23),
        mi=st.integers(min_value=0, max_value=59),
        s=st.integers(min_value=0, max_value=59),
    ),
)

_log_level = st.sampled_from(list(LogLevel))

_chunk_strategy = st.builds(
    lambda text, filename, timestamp, log_level: Chunk(
        text=text,
        metadata=ChunkMetadata(
            filename=filename,
            timestamp=timestamp,
            log_level=log_level,
        ),
    ),
    text=_chunk_text,
    filename=_filename,
    timestamp=_timestamp,
    log_level=_log_level,
)

_chunks_strategy = st.lists(_chunk_strategy, min_size=1, max_size=10)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_settings() -> Settings:
    return Settings(
        GOOGLE_API_KEY=FAKE_API_KEY,
        CHROMA_COLLECTION_NAME=f"test_{_uuid.uuid4().hex[:8]}",
        CHROMA_PERSIST_DIR=tempfile.mkdtemp(),
    )


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
        _make_fake_embedding_obj([0.1 + i * 0.001] * EMBEDDING_DIM)
        for i in range(len(texts))
    ]
    return result


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(chunks=_chunks_strategy)
def test_session_cleanup_removes_all_data(chunks: list[Chunk]) -> None:
    """Feature: semantic-log-explorer, Property 8: Limpeza de sessão remove todos os dados

    For any collection in ChromaDB with stored data, after executing session
    cleanup (delete_log), the collection must be removed.

    **Validates: Requirement 8.3**
    """
    assume(len(chunks) > 0)

    with patch("src.services.vectorstore.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = lambda **kwargs: _fake_embed_content_response(kwargs.get("contents", []))
        mock_genai.Client.return_value = mock_client
        svc = VectorStoreService(_fake_settings())
        count, collection_name = svc.add_chunks(chunks, "test.log")

    # Confirm data was actually stored before cleanup
    collection = svc._client.get_or_create_collection(name=collection_name)
    stored = collection.get()
    assert len(stored["ids"]) == len(chunks), (
        f"Expected {len(chunks)} stored documents before cleanup, got {len(stored['ids'])}"
    )

    # Execute session cleanup via delete_log
    svc.delete_log(collection_name)

    # After cleanup the collection must be gone
    remaining = svc._client.list_collections()
    remaining_names = [c.name for c in remaining]
    assert collection_name not in remaining_names, (
        f"Expected collection '{collection_name}' to be deleted, but it still exists"
    )
