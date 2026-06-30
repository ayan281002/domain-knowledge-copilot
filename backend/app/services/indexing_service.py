import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings
from app.services.chunking import recursive_char_split
from app.services.file_parser import parse_file, validate_extension
from app.services.retrieval_service import RetrievalService


class IndexingService:
    def __init__(self):
        self.settings = get_settings()
        self.retrieval = RetrievalService()

    def store_upload(self, corpus_id: int, upload_file: UploadFile) -> str:
        if not upload_file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload")

        validate_extension(upload_file.filename)
        Path(self.settings.uploads_dir).mkdir(parents=True, exist_ok=True)
        corpus_dir = Path(self.settings.uploads_dir) / str(corpus_id)
        corpus_dir.mkdir(parents=True, exist_ok=True)

        destination = corpus_dir / f"{uuid.uuid4().hex}_{upload_file.filename}"
        with destination.open("wb") as out:
            out.write(upload_file.file.read())

        return str(destination)

    def build_chunks(self, corpus_id: int, filepath: str, original_name: str) -> list[dict]:
        pages = parse_file(filepath)
        chunks: list[dict] = []

        for page in pages:
            page_num = page.get("page_number")
            text = page.get("text", "")
            pieces = recursive_char_split(
                text=text,
                chunk_size=self.settings.chunk_size,
                overlap=self.settings.chunk_overlap,
            )
            for piece in pieces:
                chunks.append(
                    {
                        "chunk_id": uuid.uuid4().hex,
                        "text": piece,
                        "source_file": original_name,
                        "page_number": page_num,
                        "corpus_id": corpus_id,
                    }
                )

        return chunks

    def index(self, corpus_id: int, filepath: str, original_name: str) -> int:
        chunks = self.build_chunks(corpus_id, filepath, original_name)
        if not chunks:
            return 0
        self.retrieval.upsert_chunks(corpus_id=corpus_id, chunks=chunks)
        return len(chunks)
