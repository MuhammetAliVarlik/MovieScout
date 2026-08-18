from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SECRET_KEY: str = "dev-secret-change-me"
    # Safe-by-default: debug mode (Werkzeug's in-browser code-execution
    # console) only turns on if .env explicitly opts in with FLASK_ENV=development.
    # run.py binds host="0.0.0.0" (needed for Docker), so a forgotten dev
    # setting here would expose that console to the whole network, not just
    # localhost — see run.py for the FLASK_ENV == "development" check.
    FLASK_ENV: str = "production"

    TMDB_API_KEY: str = ""
    TMDB_DATASET_PATH: Path = Path("./data/processed/TMDB.csv")
    TMDB_BUILD_LIMIT: int = 10000

    CHROMA_PERSIST_PATH: Path = Path("./data/chroma")

    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    LOCAL_MODEL_MAX_TOKENS: int = 512

    MAX_RECOMMENDATIONS: int = 20
    RAG_CONTEXT_FILMS: int = 10
