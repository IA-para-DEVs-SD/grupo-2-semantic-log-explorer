"""Property-based test for vectorization — embeddings and metadata correctness.

Feature: semantic-log-explorer, Property 4: Vetorização produz embeddings e metadados corretos

Para qualquer chunk gerado pelo módulo de ingestão, após vetorização, o
embedding armazenado no ChromaDB deve ter exatamente 768 dimensões e os
metadados devem conter os campos filename, timestamp e log_level.

**Validates: Requirements 2.1, 2.2**
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

_chunks_strategy = st.lists(_chunk_strategy, min_size=1, max_size=5)


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
def test_vectorization_produces_correct_embeddings_and_metadata(
    chunks: list[Chunk],
) -> None:
    """Feature: semantic-log-explorer, Property 4: Vetorização produz embeddings e metadados corretos

    For any chunk produced by the ingestion module, after vectorization the
    embedding stored in ChromaDB must have exactly 768 dimensions and the
    metadata must contain the fields filename, timestamp and log_level.

    **Validates: Requirements 2.1, 2.2**
    """
    assume(len(chunks) > 0)

    with patch("backend.src.services.vectorstore.genai") as mock_genai:
        mock_genai.embed_content.side_effect = _fake_embed_content_response
        svc = VectorStoreService(_fake_settings())
        svc.add_chunks(chunks)

    # Retrieve everything stored in the collection
    stored = svc._collection.get(include=["embeddings", "metadatas"])

    assert len(stored["ids"]) == len(chunks), (
        f"Expected {len(chunks)} stored documents, got {len(stored['ids'])}"
    )

    for i, embedding in enumerate(stored["embeddings"]):
        # Embedding must have exactly 768 dimensions
        assert len(embedding) == EMBEDDING_DIM, (
            f"Embedding {i} has {len(embedding)} dimensions, expected {EMBEDDING_DIM}"
        )

    for i, meta in enumerate(stored["metadatas"]):
        # Metadata must contain the three required fields
        assert "filename" in meta, f"Metadata {i} missing 'filename'"
        assert "timestamp" in meta, f"Metadata {i} missing 'timestamp'"
        assert "log_level" in meta, f"Metadata {i} missing 'log_level'"

        # Values must match the original chunk data
        original = chunks[i]
        assert meta["filename"] == original.metadata.filename
        assert meta["timestamp"] == (original.metadata.timestamp or "")
        assert meta["log_level"] == original.metadata.log_level.value
