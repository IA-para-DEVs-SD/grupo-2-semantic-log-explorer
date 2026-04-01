"""Property-based test for retriever — bounded result count.

Feature: semantic-log-explorer, Property 6: Retriever retorna quantidade limitada de resultados

Para qualquer pergunta enviada ao retriever com dados indexados no ChromaDB,
o número de chunks retornados deve estar entre 1 e 10 (inclusive),
respeitando o parâmetro top_k.

**Validates: Requirement 3.3**
"""

import uuid as _uuid
import tempfile
from unittest.mock import MagicMock, patch

from src.core.config import Settings
from src.models.schemas import Chunk, ChunkMetadata, LogLevel
from src.services.retriever import retrieve
from src.services.vectorstore import VectorStoreService
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EMBEDDING_DIM = 768
FAKE_API_KEY = "fake-google-api-key-for-testing"

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_question = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=200,
)

_top_k = st.integers(min_value=-10, max_value=50)

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

_chunks_strategy = st.lists(_chunk_strategy, min_size=1, max_size=15)


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
@given(
    chunks=_chunks_strategy,
    question=_question,
    top_k=_top_k,
)
def test_retriever_returns_bounded_results(
    chunks: list[Chunk],
    question: str,
    top_k: int,
) -> None:
    """Feature: semantic-log-explorer, Property 6: Retriever retorna quantidade limitada de resultados

    For any question sent to the retriever with indexed data in ChromaDB,
    the number of returned chunks must be between 1 and 10 (inclusive),
    respecting the top_k parameter.

    **Validates: Requirement 3.3**
    """
    assume(len(chunks) > 0)
    assume(len(question.strip()) > 0)

    with patch("src.services.vectorstore.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = lambda **kwargs: _fake_embed_content_response(kwargs.get("contents", []))
        mock_genai.Client.return_value = mock_client
        svc = VectorStoreService(_fake_settings())
        svc.add_chunks(chunks, "test.log")

        results = retrieve(question, svc, top_k=top_k)

    # The effective top_k after clamping is max(1, min(top_k, 10))
    effective_top_k = max(1, min(top_k, 10))
    expected_max = min(effective_top_k, len(chunks))

    # Result count must be between 1 and 10 (inclusive) and at most the
    # number of stored chunks
    assert 1 <= len(results) <= 10, (
        f"Expected between 1 and 10 results, got {len(results)}"
    )
    assert len(results) <= expected_max, (
        f"Expected at most {expected_max} results (effective_top_k={effective_top_k}, "
        f"stored={len(chunks)}), got {len(results)}"
    )

    # Every result must be a valid Chunk
    for chunk in results:
        assert isinstance(chunk, Chunk)
        assert chunk.text != ""
        assert chunk.metadata.filename != ""
        assert isinstance(chunk.metadata.log_level, LogLevel)
