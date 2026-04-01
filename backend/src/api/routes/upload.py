"""Upload route — POST /api/upload.

Recebe arquivos de log (.log, .txt, .json), valida formato e tamanho,
e orquestra o pipeline de ingestão (limpeza → sanitização → chunking → vetorização).
"""

from pathlib import Path

from src.api.dependencies import get_settings_dep, get_vectorstore_service
from src.core.config import Settings
from src.models.schemas import UploadResponse
from src.services.ingestion import process_file
from src.services.vectorstore import VectorStoreService
from fastapi import APIRouter, Depends, HTTPException, UploadFile

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile,
    settings: Settings = Depends(get_settings_dep),
    vectorstore: VectorStoreService = Depends(get_vectorstore_service),
) -> UploadResponse:
    """Upload and process a log file.

    Validates file format and size, then runs the ingestion pipeline:
    cleaning → PII sanitization → semantic chunking → vectorization.

    Args:
        file: The uploaded file (multipart/form-data).
        settings: Application settings with validation limits.
        vectorstore: VectorStore service for storing chunks.

    Returns:
        UploadResponse with status, chunk count, and filename.

    Raises:
        HTTPException 400: Invalid format or empty file.
        HTTPException 413: File exceeds size limit.
    """
    filename = file.filename or "unknown"
    extension = Path(filename).suffix.lower()

    # Validate file format
    if extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Formato não suportado. Use .log, .txt ou .json",
        )

    # Read file content to check size and emptiness
    content = await file.read()

    # Validate file is not empty
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Arquivo vazio",
        )

    # Validate file size (convert MB to bytes)
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail="Arquivo excede o limite de 50MB",
        )

    # Reset file position for processing
    await file.seek(0)

    # Process file through ingestion pipeline
    chunks = await process_file(file)

    # Store chunks in vector store
    chunk_count, collection_name = vectorstore.add_chunks(chunks, filename)

    return UploadResponse(
        status="indexed",
        chunks=chunk_count,
        filename=filename,
    )
