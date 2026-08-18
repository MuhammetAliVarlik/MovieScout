## Project Organization

```
├── Dockerfile          <- CPU-only image; pip install + `python run.py`, runs as non-root
├── docker-compose.yml  <- Single `web` service, binds ./data for persistence
├── .dockerignore       <- Keeps build context small (excludes .git, data/, etc.)
│
├── LICENSE            <- Open-source license (MIT)
├── Makefile           <- Convenience commands (make requirements/lint/format/test)
├── README.md          <- Project description, setup instructions, and usage
├── data               <- Gitignored (bar a .gitkeep) — nothing TMDB-derived is shipped
│   ├── external       <- empty
│   ├── interim        <- empty
│   ├── processed      <- TMDB.csv lands here after scripts/build_dataset.py
│   ├── chroma         <- ChromaDB index, built by scripts/build_index.py
│   └── .fetch_meta.json <- fetch timestamp, written by scripts/build_dataset.py
│
├── docs               <- Screenshots/media used by README
│
├── notebooks          <- Historical exploration/prototyping notebooks (predate scripts/build_dataset.py;
│                         preprocess.ipynb has an in-notebook note explaining it's superseded), outputs cleared
│
├── pyproject.toml     <- Project metadata + tool config (ruff, pytest)
│
├── requirements.txt   <- Runtime pip dependencies
├── requirements-dev.txt <- Dev-only tools (pytest, ruff) — not installed in the Docker image
│
├── scripts
│   ├── build_dataset.py <- Fetches a bounded, popularity-ranked subset from the TMDB API
│   ├── build_index.py   <- Embeds data/processed/TMDB.csv into ChromaDB, with progress output
│   └── setup.py          <- Runs both of the above in sequence
│
├── setup.cfg          <- flake8 configuration
│
├── run.py             <- Entry point: builds the app via app.create_app() and runs it
│
├── tests              <- Pytest suite
│   ├── conftest.py
│   ├── fixtures/TMDB.csv <- Tiny hand-authored dataset used only by tests, never real TMDB data
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
