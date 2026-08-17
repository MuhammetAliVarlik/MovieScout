## Project Organization

```
├── Dockerfile          <- CPU-only image; pip install + `python run.py`
├── docker-compose.yml  <- Single `web` service, binds ./data for persistence
├── .dockerignore       <- Keeps build context small (excludes .git, data/, etc.)
│
├── LICENSE            <- Open-source license (MIT)
├── Makefile           <- Convenience commands (make requirements/lint/format/test)
├── README.md          <- Project description, setup instructions, and usage
├── data               <- Directory for handling all data files
│   ├── external       <- Data from third party sources (e.g., raw datasets, APIs) — gitignored, empty
│   ├── interim        <- Intermediate data that has been processed or transformed but is not final yet — gitignored, empty
│   └── processed      <- The final, canonical dataset (TMDB.csv, ships with the repo)
│
├── docs               <- Screenshots/media used by README
│
├── notebooks          <- Jupyter notebooks used during initial data exploration/preprocessing
│
├── pyproject.toml     <- Project metadata + tool config (ruff, pytest)
│
├── requirements.txt   <- Runtime pip dependencies
├── requirements-dev.txt <- Dev-only tools (pytest, ruff) — not installed in the Docker image
│
├── setup.cfg          <- flake8 configuration
│
├── run.py             <- Entry point: builds the app via app.create_app() and runs it
│
├── tests              <- Pytest suite
│   ├── conftest.py
│   ├── test_letterboxd.py
│   ├── test_models.py
│   └── test_routes.py
│
└── app                <- Flask application package
    │
    ├── __init__.py             <- create_app() factory: config, extensions, blueprint registration
    ├── config.py                <- Pydantic Settings (env-driven configuration)
    ├── extensions.py             <- Shared Flask extensions (cache)
    │
    ├── blueprints
    │   ├── home                <- Search + recommendations UI (/, /search_movies, /find_similar_movies)
    │   ├── discover             <- Swipe-to-discover UI (/discover)
    │   ├── chat                 <- LLM chat UI (/chat, /chat/stream, /chat/search)
    │   └── api                  <- /api/import (Letterboxd), /api/profile, /api/watchlist/export
    │
    ├── services
    │   ├── recommendation.py    <- MovieRecommendationEngine (ChromaDB semantic search)
    │   ├── search.py             <- MovieSearchService
    │   ├── rag.py                 <- FilmRAG — local LLM chat via Ollama
    │   └── letterboxd.py          <- LetterboxdImporter — parses a Letterboxd export
    │
    ├── models
    │   └── movie.py              <- Movie, RatedMovie, TasteProfile (pydantic)
    │
    ├── static                    <- App-level static assets (CSS, JS)
    └── templates                 <- App-level templates + shared partials (navbar, modals)
```

---
