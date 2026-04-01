"""Logs route — GET /api/logs, DELETE /api/logs/{collection}.

Lista e gerencia coleções de logs armazenadas no ChromaDB.
"""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_vectorstore_service
from src.models.schemas import LogInfo
from src.services.vectorstore import VectorStoreService

router = APIRouter()


@router.get("/logs", response_model=list[LogInfo])
async def list_logs(
    vectorstore: VectorStoreService = Depends(get_vectorstore_service),
) -> list[LogInfo]:
    """List all stored log collections."""
    return vectorstore.list_logs()


@router.delete("/logs/{collection_name}")
async def delete_log(
    collection_name: str,
    vectorstore: VectorStoreService = Depends(get_vectorstore_service),
):
    """Delete a log collection."""
    vectorstore.delete_log(collection_name)
    return {"status": "deleted", "collection": collection_name}
