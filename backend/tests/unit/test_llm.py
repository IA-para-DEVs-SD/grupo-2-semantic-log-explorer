"""Unit tests for services/llm.py — LLM integration and prompt assembly."""

from unittest.mock import MagicMock, patch

import pytest
from src.core.config import Settings
from src.models.schemas import Chunk, ChunkMetadata, LogLevel
from src.services.llm import (
    SYSTEM_PROMPT,
    LLMService,
    build_prompt,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_API_KEY = "fake-google-api-key-for-testing"


def _fake_settings() -> Settings:
    return Settings(GOOGLE_API_KEY=FAKE_API_KEY)


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
# System prompt content
# ---------------------------------------------------------------------------


class TestSystemPrompt:
    def test_contains_sre_senior_role(self):
        """Prompt must instruct Gemini to act as SRE Senior."""
        assert "SRE Senior" in SYSTEM_PROMPT

    def test_contains_anti_speculation_instruction(self):
        """Prompt must instruct not to speculate when data is insufficient."""
        assert "NÃO especule" in SYSTEM_PROMPT

    def test_contains_markdown_formatting_instruction(self):
        """Prompt must instruct to format code in Markdown blocks."""
        assert "Markdown" in SYSTEM_PROMPT
        assert "```" in SYSTEM_PROMPT

    def test_contains_root_cause_instruction(self):
        """Prompt must instruct to highlight the exact log excerpt."""
        assert "Causa Raiz" in SYSTEM_PROMPT

    def test_contains_executive_summary_instruction(self):
        """Prompt must instruct concise summaries."""
        assert "Resumo" in SYSTEM_PROMPT
        assert "direto e objetivo" in SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    def test_includes_question(self):
        prompt = build_prompt("What caused the crash?", [])
        assert "What caused the crash?" in prompt

    def test_includes_chunk_text(self):
        chunk = _make_chunk(text="ERROR NullPointerException at line 42")
        prompt = build_prompt("What happened?", [chunk])
        assert "ERROR NullPointerException at line 42" in prompt

    def test_includes_chunk_metadata(self):
        chunk = _make_chunk(filename="server.log", log_level=LogLevel.CRITICAL)
        prompt = build_prompt("Explain", [chunk])
        assert "server.log" in prompt
        assert "CRITICAL" in prompt

    def test_includes_timestamp_when_present(self):
        chunk = _make_chunk(timestamp="2024-06-01 12:00:00")
        prompt = build_prompt("Explain", [chunk])
        assert "2024-06-01 12:00:00" in prompt

    def test_omits_timestamp_when_none(self):
        chunk = _make_chunk(timestamp=None)
        prompt = build_prompt("Explain", [chunk])
        # Should not contain a dangling pipe for missing timestamp
        assert "| None" not in prompt

    def test_multiple_chunks_numbered(self):
        chunks = [
            _make_chunk(text="First error"),
            _make_chunk(text="Second error"),
        ]
        prompt = build_prompt("What happened?", chunks)
        assert "Chunk 1" in prompt
        assert "Chunk 2" in prompt
        assert "First error" in prompt
        assert "Second error" in prompt

    def test_empty_chunks_shows_no_logs_message(self):
        prompt = build_prompt("Any errors?", [])
        assert "Nenhum log disponível" in prompt

    def test_has_context_and_question_sections(self):
        prompt = build_prompt("Test?", [_make_chunk()])
        assert "## Contexto dos Logs" in prompt
        assert "## Pergunta do Usuário" in prompt


# ---------------------------------------------------------------------------
# LLMService initialization
# ---------------------------------------------------------------------------


class TestLLMServiceInit:
    def test_creates_client_with_api_key(self):
        with patch("src.services.llm.genai") as mock_genai:
            svc = LLMService(_fake_settings())
            mock_genai.Client.assert_called_once_with(api_key=FAKE_API_KEY)


# ---------------------------------------------------------------------------
# generate_stream
# ---------------------------------------------------------------------------


class TestGenerateStream:
    @pytest.mark.asyncio
    async def test_yields_tokens_from_gemini(self):
        mock_chunk1 = MagicMock()
        mock_chunk1.text = "Hello "
        mock_chunk2 = MagicMock()
        mock_chunk2.text = "world"

        with patch("src.services.llm.genai") as mock_genai:
            mock_client = MagicMock()
            mock_client.models.generate_content_stream.return_value = [mock_chunk1, mock_chunk2]
            mock_genai.Client.return_value = mock_client

            svc = LLMService(_fake_settings())
            tokens = []
            async for token in svc.generate_stream("test?", [_make_chunk()]):
                tokens.append(token)

        assert tokens == ["Hello ", "world"]

    @pytest.mark.asyncio
    async def test_skips_empty_text_chunks(self):
        mock_chunk1 = MagicMock()
        mock_chunk1.text = "data"
        mock_chunk2 = MagicMock()
        mock_chunk2.text = ""
        mock_chunk3 = MagicMock()
        mock_chunk3.text = None

        with patch("src.services.llm.genai") as mock_genai:
            mock_client = MagicMock()
            mock_client.models.generate_content_stream.return_value = [mock_chunk1, mock_chunk2, mock_chunk3]
            mock_genai.Client.return_value = mock_client

            svc = LLMService(_fake_settings())
            tokens = []
            async for token in svc.generate_stream("test?", []):
                tokens.append(token)

        assert tokens == ["data"]

    @pytest.mark.asyncio
    async def test_handles_gemini_error_gracefully(self):
        with patch("src.services.llm.genai") as mock_genai:
            mock_client = MagicMock()
            mock_client.models.generate_content_stream.side_effect = RuntimeError("API down")
            mock_genai.Client.return_value = mock_client

            svc = LLMService(_fake_settings())
            tokens = []
            async for token in svc.generate_stream("test?", []):
                tokens.append(token)

        assert len(tokens) == 1
        assert "Erro ao comunicar com o serviço de IA" in tokens[0]

    @pytest.mark.asyncio
    async def test_passes_built_prompt_to_model(self):
        with patch("src.services.llm.genai") as mock_genai:
            mock_client = MagicMock()
            mock_client.models.generate_content_stream.return_value = []
            mock_genai.Client.return_value = mock_client

            svc = LLMService(_fake_settings())
            chunks = [_make_chunk(text="ERROR db timeout")]
            async for _ in svc.generate_stream("What failed?", chunks):
                pass

            call_args = mock_client.models.generate_content_stream.call_args
            prompt_sent = call_args.kwargs["contents"]
            assert "ERROR db timeout" in prompt_sent
            assert "What failed?" in prompt_sent
