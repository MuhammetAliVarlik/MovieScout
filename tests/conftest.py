import pytest
from app import create_app
from app.config import Config


@pytest.fixture()
def app():
    cfg = Config(
        SECRET_KEY="test-secret",
        TMDB_DATASET_PATH="data/processed/TMDB.csv",
        CHROMA_PERSIST_PATH="data/chroma",
        LOCAL_MODEL_PATH="models/test.gguf",
    )
    application = create_app(cfg)
    application.config["TESTING"] = True
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()
