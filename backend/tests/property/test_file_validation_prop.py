"""Property-based test for file format validation.

Feature: semantic-log-explorer, Property 1: Validação de formato de arquivo

For any file sent to the POST /api/upload endpoint, the file must be accepted
if and only if its extension is in {.log, .txt, .json}. Files with extensions
outside this set must return HTTP 400.

Validates: Requirements 1.1, 1.2
"""

import io
from unittest.mock import MagicMock, patch

from src.api.routes.upload import router as upload_router
from src.core.config import Settings
from src.models.schemas import Chunk, ChunkMetadata, LogLevel
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_EXTENSIONS = {".log", ".txt", ".json"}


# ---------------------------------------------------------------------------
# Strategies — generators for file extensions
# ---------------------------------------------------------------------------

# Strategy for valid extensions
_valid_extension_strategy = st.sampled_from(list(VALID_EXTENSIONS))

# Strategy for random invalid extensions (excluding valid ones)
# Generate extensions like .pdf, .xml, .csv, .exe, .py, etc.
_extension_chars = st.from_regex(r"[a-zA-Z0-9]{1,10}", fullmatch=True)
_invalid_extension_strategy = st.builds(
    lambda ext: f".{ext}",
    _extension_chars,
).filter(lambda ext: ext.lower() not in VALID_EXTENSIONS)

# Strategy for random filename base (without extension)
_filename_base_strategy = st.from_regex(r"[a-zA-Z0-9_-]{1,20}", fullmatch=True)

# Strategy for file content (non-empty)
_file_content_strategy = st.binary(min_size=1, max_size=1024)


# ---------------------------------------------------------------------------
# Fixtures (inline for property tests)
# ---------------------------------------------------------------------------


def create_test_app():
    """Create FastAPI app with mocked dependencies for testing."""
    from src.api.dependencies import (
        get_settings_dep,
        get_vectorstore_service,
    )

    mock_settings = Settings(
        GOOGLE_API_KEY="test-api-key",
        CHROMA_COLLECTION_NAME="test_collection",
        MAX_FILE_SIZE_MB=50,
        ALLOWED_EXTENSIONS=VALID_EXTENSIONS,
    )

    mock_vectorstore = MagicMock()
    mock_vectorstore.add_chunks.return_value = (1, "test_collection")

    test_app = FastAPI()
    test_app.include_router(upload_router, prefix="/api")

    test_app.dependency_overrides[get_settings_dep] = lambda: mock_settings
    test_app.dependency_overrides[get_vectorstore_service] = lambda: mock_vectorstore

    return test_app


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(
    filename_base=_filename_base_strategy,
    valid_extension=_valid_extension_strategy,
    file_content=_file_content_strategy,
)
def test_valid_extensions_are_accepted(
    filename_base: str,
    valid_extension: str,
    file_content: bytes,
) -> None:
    """Property 1 (valid case): files with valid extensions (.log, .txt, .json) are accepted → HTTP 200."""
    app = create_test_app()
    client = TestClient(app)

    filename = f"{filename_base}{valid_extension}"

    # Mock process_file to avoid actual processing
    with patch("src.api.routes.upload.process_file") as mock_process_file:
        mock_process_file.return_value = [
            Chunk(
                text="test log content",
                metadata=ChunkMetadata(filename=filename, log_level=LogLevel.INFO),
            ),
        ]

        files = {
            "file": (filename, io.BytesIO(file_content), "application/octet-stream")
        }
        response = client.post("/api/upload", files=files)

        assert response.status_code == 200, (
            f"Expected HTTP 200 for valid extension {valid_extension!r}, "
            f"got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert data["status"] == "indexed"
        assert data["filename"] == filename


@settings(max_examples=100)
@given(
    filename_base=_filename_base_strategy,
    invalid_extension=_invalid_extension_strategy,
    file_content=_file_content_strategy,
)
def test_invalid_extensions_are_rejected(
    filename_base: str,
    invalid_extension: str,
    file_content: bytes,
) -> None:
    """Property 1 (invalid case): files with invalid extensions are rejected → HTTP 400."""
    # Ensure the extension is truly invalid (case-insensitive check)
    assume(invalid_extension.lower() not in VALID_EXTENSIONS)

    app = create_test_app()
    client = TestClient(app)

    filename = f"{filename_base}{invalid_extension}"

    files = {"file": (filename, io.BytesIO(file_content), "application/octet-stream")}
    response = client.post("/api/upload", files=files)

    assert response.status_code == 400, (
        f"Expected HTTP 400 for invalid extension {invalid_extension!r}, "
        f"got {response.status_code}: {response.text}"
    )
    assert "Formato não suportado" in response.json()["detail"]
