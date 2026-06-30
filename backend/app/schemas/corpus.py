from datetime import datetime

from pydantic import BaseModel


class CorpusCreate(BaseModel):
    name: str
    description: str | None = None


class CorpusRead(BaseModel):
    id: int
    user_id: int
    name: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    status: str
    chunks_created: int
    filename: str
