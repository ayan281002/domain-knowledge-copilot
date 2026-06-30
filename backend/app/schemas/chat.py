from datetime import datetime

from pydantic import BaseModel


class Citation(BaseModel):
    source_file: str
    page: int | None = None
    chunk_id: str
    excerpt: str


class QueryRequest(BaseModel):
    question: str
    session_id: int | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_chunks: list[dict]
    session_id: int


class SessionCreate(BaseModel):
    corpus_id: int
    title: str | None = None


class SessionRead(BaseModel):
    id: int
    corpus_id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageRead(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    citations_json: str | None
    created_at: datetime

    class Config:
        from_attributes = True
