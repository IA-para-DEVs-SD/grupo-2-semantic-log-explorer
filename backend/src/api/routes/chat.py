"""Chat route — POST /api/chat.

Recebe perguntas em linguagem natural, orquestra o pipeline RAG
(retriever → LLM) e retorna respostas via streaming SSE.
"""

import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.src.api.dependencies import get_llm_service, get_vectorstore_service
from backend.src.models.schemas import ChatRequest
from backend.src.services.llm import LLMService
from backend.src.services.retriever import retrieve
from backend.src.services.vectorstore import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter()


async def generate_sse_stream(
    question: str,
    vectorstore: VectorStoreService,
    llm_service: LLMService,
) -> AsyncGenerator[str, None]:
    """Generate SSE-formatted stream from LLM response.

    Args:
        question: User question in natural language.
        vectorstore: VectorStore service for retrieving chunks.
        llm_service: LLM service for generating responses.

    Yields:
        SSE-formatted data events with response tokens.
    """
    # Retrieve relevant chunks from ChromaDB
    chunks = retrieve(question=question, vectorstore=vectorstore, top_k=5)

    # Generate streaming response from LLM
    async for token in llm_service.generate_stream(
        question=question,
        context_chunks=chunks,
    ):
        yield f"data: {token}\n\n"


@router.post("/chat")
async def chat(
    request: ChatRequest,
    vectorstore: VectorStoreService = Depends(get_vectorstore_service),
    llm_service: LLMService = Depends(get_llm_service),
) -> StreamingResponse:
    """Process a chat question and stream the AI response.

    Orchestrates the RAG pipeline: retrieves relevant log chunks from
    ChromaDB, passes them to the LLM with the user question, and streams
    the response via Server-Sent Events (SSE).

    Args:
        request: ChatRequest containing the user question.
        vectorstore: VectorStore service for semantic search.
        llm_service: LLM service for response generation.

    Returns:
        StreamingResponse with text/event-stream content type.

    Raises:
        HTTPException 400: No logs indexed (empty collection).
        HTTPException 502: Error communicating with AI service.
    """
    # Check if there are any indexed chunks
    try:
        # Query with a dummy embedding to check if collection has data
        # We use a zero vector just to check collection count
        test_results = vectorstore._collection.count()
        if test_results == 0:
            raise HTTPException(
                status_code=400,
                detail="Nenhum log indexado. Faça upload de um arquivo primeiro",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error checking indexed chunks: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Erro ao comunicar com o serviço de IA",
        ) from exc

    return StreamingResponse(
        generate_sse_stream(
            question=request.question,
            vectorstore=vectorstore,
            llm_service=llm_service,
        ),
        media_type="text/event-stream",
    )
