from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///./database/app.db", alias="DATABASE_URL")
    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=120, alias="JWT_EXPIRE_MINUTES")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")

    chroma_path: str = Field(default="./database/chromadb", alias="CHROMA_PATH")
    uploads_dir: str = Field(default="./uploads", alias="UPLOADS_DIR")

    embedding_provider: str = Field(default="sentence_transformers", alias="EMBEDDING_PROVIDER")
    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")

    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k_semantic: int = 20
    top_k_final: int = 5
    history_turns: int = 5

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
