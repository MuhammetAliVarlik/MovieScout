from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SECRET_KEY: str = "dev-secret-change-me"
    FLASK_ENV: str = "development"

    TMDB_API_KEY: str = ""
    TMDB_DATASET_PATH: Path = Path("./data/processed/TMDB.csv")

    CHROMA_PERSIST_PATH: Path = Path("./data/chroma")

    LOCAL_MODEL_PATH: Path = Path("./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
    LOCAL_MODEL_CONTEXT_LENGTH: int = 4096
    LOCAL_MODEL_MAX_TOKENS: int = 512

    MAX_RECOMMENDATIONS: int = 20
    RAG_CONTEXT_FILMS: int = 10
