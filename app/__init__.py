from flask import Flask
from .config import Config
from .extensions import cache


def create_app(config: Config | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    cfg = config or Config()

    app.config["SECRET_KEY"] = cfg.SECRET_KEY
    app.config["TMDB_API_KEY"] = cfg.TMDB_API_KEY
    app.config["TMDB_DATASET_PATH"] = str(cfg.TMDB_DATASET_PATH)
    app.config["CHROMA_PERSIST_PATH"] = str(cfg.CHROMA_PERSIST_PATH)
    app.config["LOCAL_MODEL_PATH"] = str(cfg.LOCAL_MODEL_PATH)
    app.config["LOCAL_MODEL_CONTEXT_LENGTH"] = cfg.LOCAL_MODEL_CONTEXT_LENGTH
    app.config["LOCAL_MODEL_MAX_TOKENS"] = cfg.LOCAL_MODEL_MAX_TOKENS
    app.config["MAX_RECOMMENDATIONS"] = cfg.MAX_RECOMMENDATIONS
    app.config["RAG_CONTEXT_FILMS"] = cfg.RAG_CONTEXT_FILMS
    app.config["CACHE_TYPE"] = "SimpleCache"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 600

    cache.init_app(app)

    # Instantiate the recommendation engine once and share it via extensions.
    # This prevents the embedding model from loading three times on startup.
    with app.app_context():
        from .services.recommendation import MovieRecommendationEngine
        engine = MovieRecommendationEngine(
            csv_file_path=app.config["TMDB_DATASET_PATH"],
            persist_path=app.config["CHROMA_PERSIST_PATH"],
        )
        app.extensions["recommendation_engine"] = engine

    from .blueprints.home.home import home_bp
    from .blueprints.discover.discover import discover_bp
    from .blueprints.chat.chat import chat_bp
    from .blueprints.api.api import api_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(discover_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
