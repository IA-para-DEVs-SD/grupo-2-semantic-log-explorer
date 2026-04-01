"""Chat route — POST /api/chat.

Recebe perguntas em linguagem natural, orquestra o pipeline RAG
(retriever → LLM) e retorna respostas como JSON.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.api.dependencies import get_llm_service, get_vectorstore_service
from src.core.security import sanitize_prompt_injection
from src.models.schemas import ChatRequest
from src.services.llm import LLMService
from src.services.retriever import retrieve
from src.services.vectorstore import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat")
async def chat(
    request: ChatRequest,
    vectorstore: VectorStoreService = Depends(get_vectorstore_service),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Process a chat question and return the AI response."""
    collection = vectorstore.get_collection_for_query(request.collection)
    if collection is None or collection.count() == 0:
        raise HTTPException(
            status_code=400,
            detail="Nenhum log indexado. Faça upload de um arquivo primeiro",
        )

    question = sanitize_prompt_injection(request.question)
    chunks = retrieve(question=question, vectorstore=vectorstore, top_k=5, collection=request.collection)

    # Collect full response
    full_response = ""
    async for token in llm_service.generate_stream(
        question=question,
        context_chunks=chunks,
    ):
        full_response += token

    return JSONResponse(content={"response": full_response})
