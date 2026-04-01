"""Property-based test for upload response fields.

Feature: semantic-log-explorer, Property 3: Resposta de upload contém campos obrigatórios

For any valid file successfully processed by the upload endpoint, the JSON response
must contain the fields `status` (equal to "indexed"), `chunks` (integer >= 1),
and `filename` (non-empty string equal to the uploaded filename).

Validates: Requirements 1.5
"""

import io
from unittest.mock import MagicMock, patch

from src.api.routes.upload import router as upload_router
from src.core.config import Settings
from src.models.schemas import Chunk, ChunkMetadata, LogLevel
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_EXTENSIONS = {".log", ".txt", ".json"}


# ---------------------------------------------------------------------------
# Strategies — generators for valid files
# ---------------------------------------------------------------------------

# Strategy for valid extensions
_valid_extension_strategy = st.sampled_from(list(VALID_EXTENSIONS))

# Strategy for random filename base (non-empty, valid characters)
_filename_base_strategy = st.from_regex(r"[a-zA-Z0-9_-]{1,20}", fullmatch=True)

# Strategy for file content (non-empty to pass validation)
_file_content_strategy = st.binary(min_size=1, max_size=1024)

# Strategy for number of chunks returned by process_file (>= 1)
_chunk_count_strategy = st.integers(min_value=1, max_value=100)


# ---------------------------------------------------------------------------
# Fixtures (inline for property tests)
# ---------------------------------------------------------------------------


def create_test_app():
    """Create FastAPI app with mocked dependencies for testing."""
    from src.api.dependencies import (
        get_settings_dep,
    )

    mock_settings = Settings(
        GOOGLE_API_KEY="test-api-key",
        CHROMA_COLLECTION_NAME="test_collection",
        MAX_FILE_SIZE_MB=50,
        ALLOWED_EXTENSIONS=VALID_EXTENSIONS,
    )

    test_app = FastAPI()
    test_app.include_router(upload_router, prefix="/api")

    test_app.dependency_overrides[get_settings_dep] = lambda: mock_settings

    return test_app


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(
    filename_base=_filename_base_strategy,
    valid_extension=_valid_extension_strategy,
    file_content=_file_content_strategy,
    chunk_count=_chunk_count_strategy,
)
def test_upload_response_contains_required_fields(
    filename_base: str,
    valid_extension: str,
    file_content: bytes,
    chunk_count: int,
) -> None:
    """Property 3: Upload response contains required fields.

    For any valid file processed successfully:
    - `status` must equal "indexed"
    - `chunks` must be an integer >= 1
    - `filename` must be a non-empty string equal to the uploaded filename
    """
    from src.api.dependencies import get_vectorstore_service

    app = create_test_app()

    # Create mock vectorstore that returns the generated chunk count
    mock_vectorstore = MagicMock()
    mock_vectorstore.add_chunks.return_value = chunk_count
    app.dependency_overrides[get_vectorstore_service] = lambda: mock_vectorstore

    client = TestClient(app)

    filename = f"{filename_base}{valid_extension}"

    # Generate chunks to be returned by process_file
    mock_chunks = [
        Chunk(
            text=f"test log content chunk {i}",
            metadata=ChunkMetadata(filename=filename, log_level=LogLevel.INFO),
        )
        for i in range(chunk_count)
    ]

    # Mock process_file to return the generated chunks
    with patch("backend.src.api.routes.upload.process_file") as mock_process_file:
        mock_process_file.return_value = mock_chunks

        files = {
            "file": (filename, io.BytesIO(file_content), "application/octet-stream")
        }
        response = client.post("/api/upload", files=files)

        # Verify HTTP 200 success
        assert response.status_code == 200, (
            f"Expected HTTP 200 for valid file, got {response.status_code}: {response.text}"
        )

        data = response.json()

        # Property 3.1: `status` field must equal "indexed"
        assert "status" in data, "Response must contain 'status' field"
        assert data["status"] == "indexed", (
            f"Expected status='indexed', got status={data['status']!r}"
        )

        # Property 3.2: `chunks` field must be an integer >= 1
        assert "chunks" in data, "Response must contain 'chunks' field"
        assert isinstance(data["chunks"], int), (
            f"Expected 'chunks' to be an integer, got {type(data['chunks']).__name__}"
        )
        assert data["chunks"] >= 1, f"Expected chunks >= 1, got chunks={data['chunks']}"
        assert data["chunks"] == chunk_count, (
            f"Expected chunks={chunk_count}, got chunks={data['chunks']}"
        )

        # Property 3.3: `filename` field must be a non-empty string equal to uploaded filename
        assert "filename" in data, "Response must contain 'filename' field"
        assert isinstance(data["filename"], str), (
            f"Expected 'filename' to be a string, got {type(data['filename']).__name__}"
        )
        assert len(data["filename"]) > 0, "Expected 'filename' to be non-empty"
        assert data["filename"] == filename, (
            f"Expected filename={filename!r}, got filename={data['filename']!r}"
        )
