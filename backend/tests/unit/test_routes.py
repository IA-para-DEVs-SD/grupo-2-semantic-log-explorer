"""Unit tests for API routes — upload and chat endpoints."""

import io
from unittest.mock import MagicMock, patch

from src.core.config import Settings
from src.models.schemas import Chunk, ChunkMetadata, LogLevel
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Upload Route Tests
# ---------------------------------------------------------------------------


class TestUploadRoute:
    """Tests for POST /api/upload endpoint."""

    def test_rejects_invalid_format(self, client):
        """Rejects file with invalid format (not .log, .txt, .json) → HTTP 400."""
        file_content = b"some log content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}

        response = client.post("/api/upload", files=files)

        assert response.status_code == 400
        assert "Formato não suportado" in response.json()["detail"]

    def test_rejects_file_exceeding_size_limit(
        self, test_app, mock_settings, mock_vectorstore, mock_llm_service
    ):
        """Rejects file > 50MB → HTTP 413."""
        from src.api.dependencies import (
            get_settings_dep,
        )

        # Override settings with 1MB limit for easier testing
        small_limit_settings = Settings(
            GOOGLE_API_KEY="test-api-key",
            CHROMA_COLLECTION_NAME="test_collection",
            MAX_FILE_SIZE_MB=1,
            ALLOWED_EXTENSIONS={".log", ".txt", ".json"},
        )
        test_app.dependency_overrides[get_settings_dep] = lambda: small_limit_settings

        client = TestClient(test_app)

        # Create file larger than 1MB
        large_content = b"x" * (2 * 1024 * 1024)  # 2MB
        files = {"file": ("large.log", io.BytesIO(large_content), "text/plain")}

        response = client.post("/api/upload", files=files)

        assert response.status_code == 413
        assert "excede o limite" in response.json()["detail"]

    def test_rejects_empty_file(self, client):
        """Rejects empty file → HTTP 400."""
        files = {"file": ("empty.log", io.BytesIO(b""), "text/plain")}

        response = client.post("/api/upload", files=files)

        assert response.status_code == 400
        assert "Arquivo vazio" in response.json()["detail"]

    @patch("backend.src.api.routes.upload.process_file")
    def test_accepts_valid_log_file(self, mock_process_file, client, mock_vectorstore):
        """Accepts valid .log file → HTTP 200 with UploadResponse."""
        mock_chunks = [
            Chunk(
                text="2024-01-15 10:00:00 INFO App started",
                metadata=ChunkMetadata(filename="app.log", log_level=LogLevel.INFO),
            ),
            Chunk(
                text="2024-01-15 10:00:01 ERROR Connection failed",
                metadata=ChunkMetadata(filename="app.log", log_level=LogLevel.ERROR),
            ),
        ]
        mock_process_file.return_value = mock_chunks

        file_content = b"2024-01-15 10:00:00 INFO App started\n2024-01-15 10:00:01 ERROR Connection failed"
        files = {"file": ("app.log", io.BytesIO(file_content), "text/plain")}

        response = client.post("/api/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "indexed"
        assert data["filename"] == "app.log"
        assert "chunks" in data

    @patch("backend.src.api.routes.upload.process_file")
    def test_accepts_valid_txt_file(self, mock_process_file, client):
        """Accepts valid .txt file → HTTP 200."""
        mock_process_file.return_value = [
            Chunk(
                text="Log entry",
                metadata=ChunkMetadata(filename="server.txt", log_level=LogLevel.INFO),
            ),
        ]

        file_content = b"Log entry"
        files = {"file": ("server.txt", io.BytesIO(file_content), "text/plain")}

        response = client.post("/api/upload", files=files)

        assert response.status_code == 200
        assert response.json()["filename"] == "server.txt"

    @patch("backend.src.api.routes.upload.process_file")
    def test_accepts_valid_json_file(self, mock_process_file, client):
        """Accepts valid .json file → HTTP 200."""
        mock_process_file.return_value = [
            Chunk(
                text='{"level": "INFO", "message": "ok"}',
                metadata=ChunkMetadata(filename="logs.json", log_level=LogLevel.INFO),
            ),
        ]

        file_content = b'[{"level": "INFO", "message": "ok"}]'
        files = {"file": ("logs.json", io.BytesIO(file_content), "application/json")}

        response = client.post("/api/upload", files=files)

        assert response.status_code == 200
        assert response.json()["filename"] == "logs.json"

    def test_rejects_unsupported_extension_xml(self, client):
        """Rejects .xml file → HTTP 400."""
        files = {
            "file": ("data.xml", io.BytesIO(b"<log>test</log>"), "application/xml")
        }

        response = client.post("/api/upload", files=files)

        assert response.status_code == 400
        assert "Formato não suportado" in response.json()["detail"]

    def test_rejects_unsupported_extension_csv(self, client):
        """Rejects .csv file → HTTP 400."""
        files = {"file": ("data.csv", io.BytesIO(b"col1,col2\nval1,val2"), "text/csv")}

        response = client.post("/api/upload", files=files)

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Chat Route Tests
# ---------------------------------------------------------------------------


class TestChatRoute:
    """Tests for POST /api/chat endpoint."""

    def test_rejects_empty_question(self, client):
        """Rejects empty question → HTTP 422 (Pydantic validation)."""
        response = client.post("/api/chat", json={"question": ""})

        assert response.status_code == 422

    def test_rejects_chat_when_no_logs_indexed(
        self, test_app, mock_settings, mock_llm_service
    ):
        """Rejects chat when no logs indexed → HTTP 400."""
        from src.api.dependencies import (
            get_vectorstore_service,
        )

        # Create vectorstore mock with empty collection
        empty_vectorstore = MagicMock()
        empty_vectorstore._collection = MagicMock()
        empty_vectorstore._collection.count.return_value = 0

        test_app.dependency_overrides[get_vectorstore_service] = lambda: (
            empty_vectorstore
        )

        client = TestClient(test_app)
        response = client.post("/api/chat", json={"question": "What errors occurred?"})

        assert response.status_code == 400
        assert "Nenhum log indexado" in response.json()["detail"]

    @patch("backend.src.api.routes.chat.retrieve")
    def test_returns_streaming_response(self, mock_retrieve, client, mock_vectorstore):
        """Returns StreamingResponse with text/event-stream content type."""
        mock_retrieve.return_value = [
            Chunk(
                text="2024-01-15 10:00:00 ERROR Connection failed",
                metadata=ChunkMetadata(filename="app.log", log_level=LogLevel.ERROR),
            ),
        ]

        response = client.post("/api/chat", json={"question": "What errors occurred?"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    @patch("backend.src.api.routes.chat.retrieve")
    def test_sse_format_has_data_prefix(self, mock_retrieve, client, mock_vectorstore):
        """SSE format has data: prefix."""
        mock_retrieve.return_value = [
            Chunk(
                text="2024-01-15 10:00:00 ERROR Connection failed",
                metadata=ChunkMetadata(filename="app.log", log_level=LogLevel.ERROR),
            ),
        ]

        response = client.post("/api/chat", json={"question": "What errors occurred?"})

        content = response.text
        # SSE events should have "data:" prefix
        assert "data:" in content

    def test_rejects_question_exceeding_max_length(self, client):
        """Rejects question exceeding max length (2000 chars) → HTTP 422."""
        long_question = "a" * 2001

        response = client.post("/api/chat", json={"question": long_question})

        assert response.status_code == 422

    def test_rejects_missing_question_field(self, client):
        """Rejects request without question field → HTTP 422."""
        response = client.post("/api/chat", json={})

        assert response.status_code == 422

    @patch("backend.src.api.routes.chat.retrieve")
    def test_accepts_valid_question(self, mock_retrieve, client, mock_vectorstore):
        """Accepts valid question and returns response."""
        mock_retrieve.return_value = [
            Chunk(
                text="2024-01-15 10:00:00 INFO App started",
                metadata=ChunkMetadata(filename="app.log", log_level=LogLevel.INFO),
            ),
        ]

        response = client.post("/api/chat", json={"question": "What happened?"})

        assert response.status_code == 200
