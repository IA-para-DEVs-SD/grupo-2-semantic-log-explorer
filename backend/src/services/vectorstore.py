"""Módulo de armazenamento vetorial com ChromaDB.

Gerencia a interface com o ChromaDB em modo efêmero para armazenamento
e busca de embeddings gerados pelo modelo gemini-embedding-001 do Google.
"""

import logging
import uuid

import chromadb
from google import genai
from google.genai import types
from fastapi import HTTPException

from src.core.config import Settings
from src.models.schemas import Chunk

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


class VectorStoreService:
    """Interface with ChromaDB for vector storage and similarity search."""

    def __init__(self, settings: Settings) -> None:
        self._genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
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
            batch_size = 5000
            for i in range(0, len(chunks), batch_size):
                self._collection.add(
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
