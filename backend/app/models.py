"""Request/response schemas."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    session_id: str | None = None
    top_k: int | None = Field(None, ge=1, le=20)


class SourceChunk(BaseModel):
    content: str
    source: str
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk] = []
    provider: str
    session_id: str | None = None


class IngestRequest(BaseModel):
    text: str | None = None
    source_name: str = "manual"


class IngestResponse(BaseModel):
    added_chunks: int
    source: str
    total_documents: int


class StatsResponse(BaseModel):
    total_chunks: int
    collection: str
    provider: str
    embedding_model: str
