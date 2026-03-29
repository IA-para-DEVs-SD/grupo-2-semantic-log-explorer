"""Módulo de busca semântica (Retriever).

Converte perguntas em vetores e busca chunks relevantes por similaridade
de cosseno no ChromaDB via VectorStoreService.
"""

import logging

from backend.src.models.schemas import Chunk, ChunkMetadata, LogLevel
from backend.src.services.vectorstore import VectorStoreService

logger = logging.getLogger(__name__)


def retrieve(
    question: str,
    vectorstore: VectorStoreService,
    top_k: int = 5,
) -> list[Chunk]:
    """Retrieve the most relevant log chunks for a natural-language question.

    Args:
        question: User question in natural language.
        vectorstore: VectorStoreService instance with indexed data.
        top_k: Maximum number of chunks to return (1–10).

    Returns:
        List of Chunk objects ordered by relevance (most similar first).
    """
    top_k = max(1, min(top_k, 10))

    query_embedding = vectorstore._generate_embeddings([question])[0]

    results = vectorstore.search(query_embedding=query_embedding, top_k=top_k)

    chunks: list[Chunk] = []
    for item in results:
        meta = item.get("metadata", {})
        log_level_raw = meta.get("log_level", "UNKNOWN")
        try:
            log_level = LogLevel(log_level_raw)
        except ValueError:
            log_level = LogLevel.UNKNOWN

        chunks.append(
            Chunk(
                text=item.get("document", ""),
                metadata=ChunkMetadata(
                    filename=meta.get("filename", ""),
                    timestamp=meta.get("timestamp") or None,
                    log_level=log_level,
                ),
            )
        )

    return chunks
