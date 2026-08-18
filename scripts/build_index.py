"""
Build the ChromaDB semantic search index from data/processed/TMDB.csv.

This is a one-time (or occasional, after re-fetching the dataset) setup
step, run explicitly rather than silently on app startup, so the multi-
minute embedding pass over a large dataset has visible progress instead
of just looking like the app is hanging.

Usage:
    python scripts/build_index.py
"""

from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import Config
from app.services.recommendation import MovieRecommendationEngine


def main() -> None:
    cfg = Config()

    print(f"Loading dataset from {cfg.TMDB_DATASET_PATH}...")
    engine = MovieRecommendationEngine(
        csv_file_path=str(cfg.TMDB_DATASET_PATH),
        persist_path=str(cfg.CHROMA_PERSIST_PATH),
        require_populated=False,
    )

    row_count = len(engine.df) if engine.df is not None else 0
    print(f"Embedding {row_count} movies into ChromaDB (this can take a few minutes)...")

    start = time.time()
    engine.populate(batch_size=500, show_progress=True)
    elapsed = time.time() - start

    print(
        f"\nDone. Indexed {row_count} movies into collection "
        f"'{engine.collection.name}' at {cfg.CHROMA_PERSIST_PATH} in {elapsed:.1f}s."
    )


if __name__ == "__main__":
    main()
