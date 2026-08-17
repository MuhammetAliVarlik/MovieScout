from pathlib import Path

import pytest
from app import create_app
from app.config import Config
from app.services.recommendation import MovieRecommendationEngine

FIXTURE_CSV = str(Path(__file__).parent / "fixtures" / "TMDB.csv")


@pytest.fixture(scope="session")
def _populated_chroma_dir(tmp_path_factory):
    """
    Build a tiny local embedding index once per test session, from the
    hand-authored fixture CSV — never the real dataset, never a network
    call. Session-scoped so the (still local, still fast) embedding pass
    only runs once instead of once per test.
    """
    chroma_dir = tmp_path_factory.mktemp("chroma")
    engine = MovieRecommendationEngine(
        csv_file_path=FIXTURE_CSV,
        persist_path=str(chroma_dir),
        require_populated=False,
    )
    engine.populate(show_progress=False)
    return str(chroma_dir)


@pytest.fixture()
def app(_populated_chroma_dir):
    cfg = Config(
        SECRET_KEY="test-secret",
        TMDB_DATASET_PATH=FIXTURE_CSV,
        CHROMA_PERSIST_PATH=_populated_chroma_dir,
    )
    application = create_app(cfg)
    application.config["TESTING"] = True
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()
