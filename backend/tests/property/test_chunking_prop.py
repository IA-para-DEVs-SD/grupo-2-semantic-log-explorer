"""Property-based test for semantic chunking — stack trace preservation.

Feature: semantic-log-explorer, Property 2: Chunking preserva stack traces completos

For any log file containing stack traces, after semantic chunking, each stack
trace must be fully contained within a single chunk, without being split
across different chunks.

**Validates: Requirements 1.6**
"""

import asyncio
import io

from src.services.ingestion import process_file
from fastapi import UploadFile
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Strategies — generators for synthetic log content with stack traces
# ---------------------------------------------------------------------------

_timestamp_strategy = st.builds(
    lambda y, mo, d, h, mi, s: f"{y:04d}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}",
    y=st.integers(min_value=2020, max_value=2025),
    mo=st.integers(min_value=1, max_value=12),
    d=st.integers(min_value=1, max_value=28),
    h=st.integers(min_value=0, max_value=23),
    mi=st.integers(min_value=0, max_value=59),
    s=st.integers(min_value=0, max_value=59),
)

_log_level = st.sampled_from(["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])

_log_message = st.from_regex(r"[A-Za-z ]{3,30}", fullmatch=True)

_log_line_strategy = st.builds(
    lambda ts, lvl, msg: f"{ts} {lvl} {msg}",
    ts=_timestamp_strategy,
    lvl=_log_level,
    msg=_log_message,
)

_module_name = st.from_regex(r"[a-z_]{3,10}", fullmatch=True)
_line_number = st.integers(min_value=1, max_value=999)

_exception_type = st.sampled_from(
    [
        "ValueError",
        "TypeError",
        "RuntimeError",
        "KeyError",
        "AttributeError",
        "IndexError",
        "IOError",
        "ConnectionError",
        "TimeoutError",
        "FileNotFoundError",
    ]
)

_exception_message = st.from_regex(r"[a-z ]{3,20}", fullmatch=True)


@st.composite
def _stack_trace_strategy(draw):
    """Generate a complete Python-style stack trace."""
    num_frames = draw(st.integers(min_value=1, max_value=5))
    lines = ["Traceback (most recent call last):"]
    for _ in range(num_frames):
        mod = draw(_module_name)
        lineno = draw(_line_number)
        func = draw(_module_name)
        lines.append(f'  File "/app/{mod}.py", line {lineno}, in {func}')
        code_line = draw(st.from_regex(r"[a-z_]+\(\)", fullmatch=True))
        lines.append(f"    {code_line}")
    exc_type = draw(_exception_type)
    exc_msg = draw(_exception_message)
    lines.append(f"{exc_type}: {exc_msg}")
    return "\n".join(lines)


@st.composite
def _log_with_stack_traces(draw):
    """Generate a synthetic log file containing normal log lines and stack traces.

    Returns a tuple of (log_content, list_of_stack_trace_strings).
    """
    num_sections = draw(st.integers(min_value=1, max_value=4))
    all_lines: list[str] = []
    stack_traces: list[str] = []

    for _ in range(num_sections):
        # Some normal log lines before the stack trace
        prefix_count = draw(st.integers(min_value=1, max_value=3))
        for _ in range(prefix_count):
            all_lines.append(draw(_log_line_strategy))

        # An ERROR log line that precedes the stack trace
        ts = draw(_timestamp_strategy)
        err_msg = draw(_log_message)
        all_lines.append(f"{ts} ERROR {err_msg}")

        # The stack trace itself
        trace = draw(_stack_trace_strategy())
        stack_traces.append(trace)
        all_lines.append(trace)

    # Some trailing normal log lines
    suffix_count = draw(st.integers(min_value=0, max_value=2))
    for _ in range(suffix_count):
        all_lines.append(draw(_log_line_strategy))

    return "\n".join(all_lines), stack_traces


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_upload(content: str, filename: str = "app.log") -> UploadFile:
    """Create a fake UploadFile from a string."""
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content.encode("utf-8")),
    )


def _run_async(coro):
    """Run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


@settings(max_examples=200)
@given(data=_log_with_stack_traces())
def test_chunking_preserves_complete_stack_traces(
    data: tuple[str, list[str]],
) -> None:
    """Feature: semantic-log-explorer, Property 2: Chunking preserva stack traces completos

    For any log file containing stack traces, after semantic chunking, each
    stack trace must be fully contained within a single chunk, without being
    split across different chunks.

    **Validates: Requirements 1.6**
    """
    log_content, stack_traces = data

    assume(len(stack_traces) > 0)
    assume(len(log_content.strip()) > 0)

    upload = _make_upload(log_content)
    chunks = _run_async(process_file(upload))

    assert len(chunks) > 0, "Expected at least one chunk from non-empty log"

    all_chunk_texts = [chunk.text for chunk in chunks]

    for trace in stack_traces:
        # Each line of the stack trace must appear in at least one chunk.
        # We check that ALL lines of a given trace are in the SAME chunk.
        # Note: chunk text is stripped by _flush_chunk, so we strip trace
        # lines for comparison as well.
        trace_lines = [line.strip() for line in trace.splitlines() if line.strip()]

        # Find which chunks contain the first line of this trace
        containing_chunks = [
            idx for idx, text in enumerate(all_chunk_texts) if trace_lines[0] in text
        ]

        assert len(containing_chunks) >= 1, (
            f"Stack trace first line not found in any chunk: {trace_lines[0]!r}"
        )

        # Verify all lines of the trace are in the same chunk
        for chunk_idx in containing_chunks:
            chunk_text = all_chunk_texts[chunk_idx]
            all_lines_present = all(line in chunk_text for line in trace_lines)
            if all_lines_present:
                break
        else:
            # No single chunk contains all lines of this stack trace
            missing_by_chunk = {}
            for chunk_idx in containing_chunks:
                chunk_text = all_chunk_texts[chunk_idx]
                missing = [l for l in trace_lines if l not in chunk_text]
                missing_by_chunk[chunk_idx] = missing

            assert False, (
                f"Stack trace split across chunks. "
                f"Trace lines: {trace_lines!r}. "
                f"Missing lines per chunk: {missing_by_chunk}"
            )
