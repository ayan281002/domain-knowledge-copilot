from functools import lru_cache

from openai import OpenAI
from sentence_transformers import SentenceTransformer

from app.config import get_settings


class EmbeddingService:
    def __init__(self):
        self.settings = get_settings()
        self.provider = self.settings.embedding_provider.lower()
        self._openai = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None
        self._st_model = None

    @property
    def dimensions(self) -> int:
        return 1536 if self.provider == "openai" else 384

    def _ensure_st(self):
        if self._st_model is None:
            self._st_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self.provider == "openai":
            if not self._openai:
                raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
            response = self._openai.embeddings.create(model="text-embedding-3-small", input=texts)
            return [item.embedding for item in response.data]

        self._ensure_st()
        vectors = self._st_model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
