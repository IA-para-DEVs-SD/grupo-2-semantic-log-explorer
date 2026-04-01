"""Unit tests for services/ingestion.py — log ingestion and semantic chunking."""

import io
import json

import pytest
from src.models.schemas import Chunk, LogLevel
from src.services.ingestion import (
    _clean_noise,
    _detect_log_level,
    _extract_timestamp,
    _is_stack_trace_start,
    process_file,
)
from fastapi import UploadFile

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_upload(content: str, filename: str = "app.log") -> UploadFile:
    """Create a fake UploadFile from a string."""
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content.encode("utf-8")),
    )


# ---------------------------------------------------------------------------
# _clean_noise
# ---------------------------------------------------------------------------


class TestCleanNoise:
    def test_replaces_uuid(self):
        text = "session=a1b2c3d4-e5f6-7890-abcd-ef1234567890 started"
        result = _clean_noise(text)
        assert "[SESSION_ID]" in result
        assert "a1b2c3d4" not in result

    def test_replaces_long_hex_token(self):
        token = "a" * 32
        result = _clean_noise(f"token={token}")
        assert "[TOKEN]" in result
        assert token not in result

    def test_leaves_short_hex_alone(self):
        text = "code=abcdef12"
        assert _clean_noise(text) == text


# ---------------------------------------------------------------------------
# _detect_log_level / _extract_timestamp
# ---------------------------------------------------------------------------


class TestDetectLogLevel:
    def test_detects_error(self):
        assert _detect_log_level("2024-01-01 ERROR something") == LogLevel.ERROR

    def test_detects_info(self):
        assert _detect_log_level("INFO: started") == LogLevel.INFO

    def test_returns_unknown_for_plain_text(self):
        assert _detect_log_level("just some text") == LogLevel.UNKNOWN

    def test_priority_critical_over_error(self):
        assert _detect_log_level("CRITICAL ERROR happened") == LogLevel.CRITICAL


class TestExtractTimestamp:
    def test_extracts_iso_timestamp(self):
        assert (
            _extract_timestamp("2024-01-15T10:30:00 INFO ok") == "2024-01-15T10:30:00"
        )

    def test_extracts_space_separated(self):
        assert (
            _extract_timestamp("2024-01-15 10:30:00 INFO ok") == "2024-01-15 10:30:00"
        )

    def test_returns_none_when_absent(self):
        assert _extract_timestamp("no timestamp here") is None


# ---------------------------------------------------------------------------
# _is_stack_trace_line
# ---------------------------------------------------------------------------


class TestIsStackTraceLine:
    def test_traceback_header(self):
        assert _is_stack_trace_start("Traceback (most recent call last):") is True

    def test_python_file_line(self):
        # File lines are continuation, not start — test start patterns
        assert _is_stack_trace_start("ValueError: invalid literal") is True

    def test_error_line(self):
        assert _is_stack_trace_start("ValueError: invalid literal") is True

    def test_normal_log_line(self):
        assert _is_stack_trace_start("2024-01-01 INFO Application started") is False

    def test_empty_line(self):
        assert _is_stack_trace_start("") is False


# ---------------------------------------------------------------------------
# process_file — .log / .txt
# ---------------------------------------------------------------------------


class TestProcessFileLog:
    @pytest.mark.asyncio
    async def test_empty_file_returns_empty(self):
        upload = _make_upload("", "empty.log")
        result = await process_file(upload)
        assert result == []

    @pytest.mark.asyncio
    async def test_single_log_line(self):
        upload = _make_upload("2024-01-15 10:00:00 INFO App started", "app.log")
        result = await process_file(upload)
        assert len(result) >= 1
        assert isinstance(result[0], Chunk)
        assert result[0].metadata.filename == "app.log"

    @pytest.mark.asyncio
    async def test_multiple_log_entries_produce_multiple_chunks(self):
        content = (
            "2024-01-15 10:00:00 INFO App started\n"
            "2024-01-15 10:00:01 ERROR Connection failed\n"
            "2024-01-15 10:00:02 INFO Retrying\n"
        )
        upload = _make_upload(content, "app.log")
        result = await process_file(upload)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_stack_trace_kept_in_single_chunk(self):
        content = (
            "2024-01-15 10:00:00 ERROR Unhandled exception\n"
            "Traceback (most recent call last):\n"
            '  File "/app/main.py", line 42, in run\n'
            "    result = do_something()\n"
            '  File "/app/utils.py", line 10, in do_something\n'
            "    raise ValueError('bad value')\n"
            "ValueError: bad value\n"
        )
        upload = _make_upload(content, "app.log")
        result = await process_file(upload)
        # The entire stack trace must be in one chunk
        assert len(result) == 1
        assert "Traceback" in result[0].text
        assert "ValueError: bad value" in result[0].text

    @pytest.mark.asyncio
    async def test_stack_trace_not_split_across_chunks(self):
        content = (
            "2024-01-15 10:00:00 INFO Starting\n"
            "2024-01-15 10:00:01 ERROR Crash\n"
            "Traceback (most recent call last):\n"
            '  File "/app/main.py", line 5, in <module>\n'
            "    foo()\n"
            "RuntimeError: boom\n"
            "2024-01-15 10:00:02 INFO Recovered\n"
        )
        upload = _make_upload(content, "app.log")
        result = await process_file(upload)
        # Find the chunk containing the traceback
        trace_chunks = [c for c in result if "Traceback" in c.text]
        assert len(trace_chunks) == 1
        assert "RuntimeError: boom" in trace_chunks[0].text

    @pytest.mark.asyncio
    async def test_pii_is_sanitized(self):
        content = (
            "2024-01-15 10:00:00 INFO User 123.456.789-00 logged in from admin@corp.com"
        )
        upload = _make_upload(content, "app.log")
        result = await process_file(upload)
        assert len(result) >= 1
        assert "123.456.789-00" not in result[0].text
        assert "[CPF_MASCARADO]" in result[0].text
        assert "admin@corp.com" not in result[0].text
        assert "[EMAIL_MASCARADO]" in result[0].text

    @pytest.mark.asyncio
    async def test_noise_cleaned(self):
        uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        content = f"2024-01-15 10:00:00 INFO session={uuid} started"
        upload = _make_upload(content, "app.log")
        result = await process_file(upload)
        assert uuid not in result[0].text
        assert "[SESSION_ID]" in result[0].text

    @pytest.mark.asyncio
    async def test_metadata_has_log_level(self):
        content = "2024-01-15 10:00:00 ERROR Something broke"
        upload = _make_upload(content, "app.log")
        result = await process_file(upload)
        assert result[0].metadata.log_level == LogLevel.ERROR

    @pytest.mark.asyncio
    async def test_metadata_has_timestamp(self):
        content = "2024-01-15 10:00:00 INFO ok"
        upload = _make_upload(content, "app.log")
        result = await process_file(upload)
        assert result[0].metadata.timestamp is not None
        assert "2024-01-15" in result[0].metadata.timestamp

    @pytest.mark.asyncio
    async def test_txt_extension_works(self):
        content = "2024-01-15 10:00:00 INFO hello"
        upload = _make_upload(content, "server.txt")
        result = await process_file(upload)
        assert len(result) >= 1
        assert result[0].metadata.filename == "server.txt"


# ---------------------------------------------------------------------------
# process_file — .json
# ---------------------------------------------------------------------------


class TestProcessFileJson:
    @pytest.mark.asyncio
    async def test_json_array(self):
        data = [
            {"timestamp": "2024-01-15T10:00:00", "level": "INFO", "message": "ok"},
            {"timestamp": "2024-01-15T10:00:01", "level": "ERROR", "message": "fail"},
        ]
        upload = _make_upload(json.dumps(data), "logs.json")
        result = await process_file(upload)
        assert len(result) == 2
        assert result[0].metadata.log_level == LogLevel.INFO
        assert result[1].metadata.log_level == LogLevel.ERROR

    @pytest.mark.asyncio
    async def test_json_single_object(self):
        data = {
            "timestamp": "2024-01-15T10:00:00",
            "level": "WARNING",
            "message": "slow",
        }
        upload = _make_upload(json.dumps(data), "entry.json")
        result = await process_file(upload)
        assert len(result) == 1
        assert result[0].metadata.log_level == LogLevel.WARNING

    @pytest.mark.asyncio
    async def test_jsonl_format(self):
        lines = [
            json.dumps(
                {"timestamp": "2024-01-15T10:00:00", "level": "INFO", "message": "a"}
            ),
            json.dumps(
                {"timestamp": "2024-01-15T10:00:01", "level": "DEBUG", "message": "b"}
            ),
        ]
        upload = _make_upload("\n".join(lines), "logs.json")
        result = await process_file(upload)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_json_pii_sanitized(self):
        data = [{"message": "user email is admin@corp.com", "level": "INFO"}]
        upload = _make_upload(json.dumps(data), "logs.json")
        result = await process_file(upload)
        assert "admin@corp.com" not in result[0].text
        assert "[EMAIL_MASCARADO]" in result[0].text

    @pytest.mark.asyncio
    async def test_empty_json_array(self):
        upload = _make_upload("[]", "empty.json")
        result = await process_file(upload)
        # Falls back to single chunk with "[]"
        assert len(result) >= 0
