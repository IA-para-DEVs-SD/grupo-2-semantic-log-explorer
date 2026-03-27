"""Chat route — POST /api/chat."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
async def chat():
    """Placeholder — will be implemented in task 7.2."""
    raise NotImplementedError
