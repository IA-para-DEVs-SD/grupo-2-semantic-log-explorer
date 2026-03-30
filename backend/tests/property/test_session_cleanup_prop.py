"""Property-based test for session cleanup — clearing collection removes all data.

Feature: semantic-log-explorer, Property 8: Limpeza de sessão remove todos os dados

Para qualquer coleção no ChromaDB com dados armazenados, após a execução da
limpeza de sessão, a coleção deve estar vazia (zero documentos).

**Validates: Requirement 8.3**
"""

import uuid as _uuid
from unittest.mock import patch

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from backend.src.core.config import Settings
from backend.src.models.schemas import Chunk, ChunkMetadata, LogLevel
from backend.src.services.vectorstore import VectorStoreService

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
    )


def _fake_embed_content_response(*, model=None, content=None, **kwargs):
    """Build a fake response matching google.generativeai.embed_content output."""
    texts = content
    if isinstance(texts, str):
        return {"embedding": [0.1] * EMBEDDING_DIM}
    return {"embedding": [[0.1 + i * 0.001] * EMBEDDING_DIM for i in range(len(texts))]}


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(chunks=_chunks_strategy)
def test_session_cleanup_removes_all_data(chunks: list[Chunk]) -> None:
    """Feature: semantic-log-explorer, Property 8: Limpeza de sessão remove todos os dados

    For any collection in ChromaDB with stored data, after executing session
    cleanup, the collection must be empty (zero documents).

    **Validates: Requirement 8.3**
    """
    assume(len(chunks) > 0)

    with patch("backend.src.services.vectorstore.genai") as mock_genai:
        mock_genai.embed_content.side_effect = _fake_embed_content_response
        svc = VectorStoreService(_fake_settings())
        svc.add_chunks(chunks)

    # Confirm data was actually stored before cleanup
    stored = svc._collection.get()
    assert len(stored["ids"]) == len(chunks), (
        f"Expected {len(chunks)} stored documents before cleanup, got {len(stored['ids'])}"
    )

    # Execute session cleanup
    svc.clear_collection()

    # After cleanup the collection must be empty
    after = svc._collection.get()
    assert len(after["ids"]) == 0, (
        f"Expected 0 documents after cleanup, got {len(after['ids'])}"
    )
