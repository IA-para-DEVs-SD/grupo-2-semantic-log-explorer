"""Upload route — POST /api/upload."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/upload")
async def upload_file():
    """Placeholder — will be implemented in task 7.1."""
    raise NotImplementedError
