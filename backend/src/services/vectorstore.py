"""Módulo de armazenamento vetorial com ChromaDB.

Gerencia a interface com o ChromaDB em modo persistente para armazenamento
e busca de embeddings gerados pelo modelo gemini-embedding-001 do Google.
Suporta múltiplas coleções (uma por arquivo de log).
"""

import logging
import re
import uuid
from datetime import datetime, timezone

import chromadb
from fastapi import HTTPException
from google import genai
from google.genai import types

from src.core.config import Settings
from src.models.schemas import Chunk, LogInfo

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


def _sanitize_collection_name(name: str) -> str:
    """Sanitize a filename into a valid ChromaDB collection name."""
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name or not name[0].isalpha():
        name = "log_" + name
    return name[:60]


class VectorStoreService:
    """Interface with ChromaDB for persistent vector storage and similarity search."""

    def __init__(self, settings: Settings) -> None:
        self._genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        try:
            self._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        except Exception as exc:
            logger.error("Failed to initialise ChromaDB: %s", exc)
            raise HTTPException(
                status_code=503,
                detail="Serviço de armazenamento vetorial indisponível",
            ) from exc

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection by name."""
        return self._client.get_or_create_collection(name=name)

    def list_logs(self) -> list[LogInfo]:
        """List all stored log collections with metadata."""
        collections = self._client.list_collections()
        logs: list[LogInfo] = []
        for col in collections:
            meta = col.metadata or {}
            logs.append(
                LogInfo(
                    collection=col.name,
                    filename=meta.get("filename", col.name),
                    chunks=col.count(),
                    uploaded_at=meta.get("uploaded_at", ""),
                )
            )
        return logs

    def delete_log(self, collection_name: str) -> None:
        """Delete a log collection by name."""
        try:
            self._client.delete_collection(name=collection_name)
        except Exception as exc:
            logger.error("Failed to delete collection %s: %s", collection_name, exc)
            raise HTTPException(status_code=404, detail="Coleção não encontrada") from exc

    def get_collection_for_query(self, collection_name: str | None = None):
        """Get a collection for querying. If none specified, use the first available."""
        if collection_name:
            try:
                return self._client.get_collection(name=collection_name)
            except Exception as exc:
                raise HTTPException(status_code=404, detail="Coleção não encontrada") from exc
        # Fallback: use first collection
        collections = self._client.list_collections()
        if not collections:
            return None
        return collections[0]

    # ------------------------------------------------------------------
    # Embedding helpers
    # ------------------------------------------------------------------

    def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts via gemini-embedding-001."""
        try:
            all_embeddings: list[list[float]] = []
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                result = self._genai_client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
                )
                all_embeddings.extend(e.values for e in result.embeddings)
            return all_embeddings
        except Exception as exc:
            logger.error("Embedding generation failed: %s", exc)
            raise HTTPException(status_code=502, detail="Erro ao gerar embeddings") from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: list[Chunk], filename: str) -> tuple[int, str]:
        """Add chunks to a new collection named after the file.

        Returns tuple of (chunk_count, collection_name).
        """
        if not chunks:
            return 0, ""

        collection_name = _sanitize_collection_name(filename)
        now = datetime.now(timezone.utc).isoformat()

        collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"filename": filename, "uploaded_at": now},
        )

        texts = [chunk.text for chunk in chunks]
        embeddings = self._generate_embeddings(texts)

        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [
            {
                "filename": chunk.metadata.filename,
                "timestamp": chunk.metadata.timestamp or "",
                "log_level": chunk.metadata.log_level.value,
            }
            for chunk in chunks
        ]

        try:
            batch_size = 5000
            for i in range(0, len(chunks), batch_size):
                collection.add(
                    ids=ids[i : i + batch_size],
                    embeddings=embeddings[i : i + batch_size],
                    documents=texts[i : i + batch_size],
                    metadatas=metadatas[i : i + batch_size],
                )
        except Exception as exc:
            logger.error("ChromaDB add failed: %s", exc)
            raise HTTPException(
                status_code=503,
                detail="Serviço de armazenamento vetorial indisponível",
            ) from exc

        return len(chunks), collection_name

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        collection_name: str | None = None,
    ) -> list[dict]:
        """Search a collection by cosine similarity."""
        collection = self.get_collection_for_query(collection_name)
        if collection is None:
            return []

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )
        except Exception as exc:
            logger.error("ChromaDB search failed: %s", exc)
            raise HTTPException(
                status_code=503,
                detail="Serviço de armazenamento vetorial indisponível",
            ) from exc

        items: list[dict] = []
        if not results or not results.get("ids"):
            return items

        ids = results["ids"][0]
        documents = results["documents"][0] if results.get("documents") else []
        metadatas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else []

        for i, doc_id in enumerate(ids):
            items.append(
                {
                    "id": doc_id,
                    "document": documents[i] if i < len(documents) else "",
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else None,
                }
            )

        return items
