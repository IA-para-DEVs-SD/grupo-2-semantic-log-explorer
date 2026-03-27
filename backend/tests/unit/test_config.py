"""Unit tests for core/config.py — Settings class."""

import pytest
from pydantic import ValidationError

from backend.src.core.config import Settings


class TestSettings:
    """Tests for the Settings configuration class."""

    def test_fails_without_google_api_key(self, monkeypatch):
        """Settings must raise an error when GOOGLE_API_KEY is not defined."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        with pytest.raises(ValidationError):
            Settings(_env_file=None)

    def test_fails_with_empty_google_api_key(self, monkeypatch):
        """Settings must raise an error when GOOGLE_API_KEY is empty."""
        monkeypatch.setenv("GOOGLE_API_KEY", "   ")

        with pytest.raises(ValidationError, match="GOOGLE_API_KEY"):
            Settings(_env_file=None)

    def test_loads_google_api_key_from_env(self, monkeypatch):
        """Settings must load GOOGLE_API_KEY from environment."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")

        s = Settings(_env_file=None)
        assert s.GOOGLE_API_KEY == "test-key-123"

    def test_strips_whitespace_from_api_key(self, monkeypatch):
        """Settings must strip leading/trailing whitespace from GOOGLE_API_KEY."""
        monkeypatch.setenv("GOOGLE_API_KEY", "  my-key  ")

        s = Settings(_env_file=None)
        assert s.GOOGLE_API_KEY == "my-key"

    def test_default_values(self, monkeypatch):
        """Settings must have correct defaults for optional fields."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

        s = Settings(_env_file=None)
        assert s.CHROMA_COLLECTION_NAME == "log_chunks"
        assert s.MAX_FILE_SIZE_MB == 50
        assert s.ALLOWED_EXTENSIONS == {".log", ".txt", ".json"}

    def test_overrides_defaults_from_env(self, monkeypatch):
        """Settings must allow overriding defaults via environment variables."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        monkeypatch.setenv("CHROMA_COLLECTION_NAME", "custom_collection")
        monkeypatch.setenv("MAX_FILE_SIZE_MB", "100")

        s = Settings(_env_file=None)
        assert s.CHROMA_COLLECTION_NAME == "custom_collection"
        assert s.MAX_FILE_SIZE_MB == 100
