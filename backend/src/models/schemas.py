from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class ChunkMetadata(BaseModel):
    filename: str
    timestamp: Optional[str] = None
    log_level: LogLevel = LogLevel.UNKNOWN


class Chunk(BaseModel):
    text: str
    metadata: ChunkMetadata


class UploadResponse(BaseModel):
    status: str = "indexed"
    chunks: int
    filename: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class ErrorResponse(BaseModel):
    detail: str
