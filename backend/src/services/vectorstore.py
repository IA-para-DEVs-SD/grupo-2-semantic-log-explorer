"""Módulo de armazenamento vetorial com ChromaDB.

Gerencia a interface com o ChromaDB em modo efêmero para armazenamento
e busca de embeddings gerados pelo modelo text-embedding-004 do Google.
"""

import logging
import uuid

import chromadb
import google.generativeai as genai
from fastapi import HTTPException

from backend.src.core.config import Settings
from backend.src.models.schemas import Chunk

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "models/text-embedding-004"
EMBEDDING_DIMENSIONS = 768


class VectorStoreService:
    """Interface with ChromaDB for vector storage and similarity search."""

    def __init__(self, settings: Settings) -> None:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self._collection_name = settings.CHROMA_COLLECTION_NAME
        try:
            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
            )
        except Exception as exc:
            logger.error("Failed to initialise ChromaDB: %s", exc)
            raise HTTPException(
                status_code=503,
                detail="Serviço de armazenamento vetorial indisponível",
            ) from exc

    # ------------------------------------------------------------------
    # Embedding helpers
    # ------------------------------------------------------------------

    def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts via text-embedding-004."""
        try:
            response = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=texts,
            )
            return response["embedding"]
        except Exception as exc:
            logger.error("Embedding generation failed: %s", exc)
            raise HTTPException(
                status_code=502,
                detail="Erro ao gerar embeddings",
            ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: list[Chunk]) -> int:
        """Add chunks to the ChromaDB collection.

        Generates embeddings, assigns UUIDs and stores documents with
        metadata (filename, timestamp, log_level).

        Returns the number of chunks added.
        """
        if not chunks:
            return 0

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
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
        except Exception as exc:
            logger.error("ChromaDB add failed: %s", exc)
            raise HTTPException(
                status_code=503,
                detail="Serviço de armazenamento vetorial indisponível",
            ) from exc

        return len(chunks)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        """Search the collection by cosine similarity.

        Args:
            query_embedding: Pre-computed embedding vector for the query.
            top_k: Maximum number of results to return.

        Returns:
            List of dicts with keys: id, document, metadata, distance.
        """
        try:
            results = self._collection.query(
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

    def clear_collection(self) -> None:
        """Delete and recreate the collection, removing all stored data."""
        try:
            self._client.delete_collection(name=self._collection_name)
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
            )
        except Exception as exc:
            logger.error("ChromaDB clear failed: %s", exc)
            raise HTTPException(
                status_code=503,
                detail="Serviço de armazenamento vetorial indisponível",
            ) from exc
