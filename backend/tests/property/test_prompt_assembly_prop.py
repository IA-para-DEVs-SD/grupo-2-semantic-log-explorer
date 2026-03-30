"""Property-based test for prompt assembly — role and context inclusion.

Feature: semantic-log-explorer, Property 7: Montagem do prompt inclui papel e contexto

Para qualquer conjunto de chunks recuperados e uma pergunta do usuário,
o prompt montado pelo Serviço_LLM deve conter a instrução de papel
(Engenheiro de SRE Senior) e o texto de todos os chunks fornecidos como contexto.

**Validates: Requirements 12.1, 12.2**
"""

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from backend.src.models.schemas import Chunk, ChunkMetadata, LogLevel
from backend.src.services.llm import SYSTEM_PROMPT, build_prompt

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_question = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=200,
)

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
# Property test
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(
    chunks=_chunks_strategy,
    question=_question,
)
def test_prompt_includes_role_and_all_chunk_context(
    chunks: list[Chunk],
    question: str,
) -> None:
    """Feature: semantic-log-explorer, Property 7: Montagem do prompt inclui papel e contexto

    For any set of retrieved chunks and a user question, the prompt assembled
    by the LLM service must contain the SRE Senior role instruction and the
    text of all chunks provided as context.

    **Validates: Requirements 12.1, 12.2**
    """
    assume(len(chunks) > 0)
    assume(len(question.strip()) > 0)

    # Verify system prompt contains the SRE Senior role
    assert "SRE Senior" in SYSTEM_PROMPT, (
        "System prompt must contain the SRE Senior role instruction"
    )

    # Build the user prompt with context
    prompt = build_prompt(question, chunks)

    # The prompt must contain the user's question
    assert question in prompt, f"Prompt must contain the user question: {question!r}"

    # The prompt must contain the text of every chunk
    for i, chunk in enumerate(chunks):
        assert chunk.text in prompt, (
            f"Prompt must contain text of chunk {i}: {chunk.text!r}"
        )

    # The prompt must contain metadata for every chunk
    for i, chunk in enumerate(chunks):
        assert chunk.metadata.filename in prompt, (
            f"Prompt must contain filename of chunk {i}: {chunk.metadata.filename!r}"
        )
        assert chunk.metadata.log_level.value in prompt, (
            f"Prompt must contain log_level of chunk {i}: {chunk.metadata.log_level.value!r}"
        )
