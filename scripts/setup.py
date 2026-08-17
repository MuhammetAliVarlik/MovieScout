"""
Run both setup steps in sequence: fetch the dataset from TMDB, then build
the semantic search index from it.

Usage:
    python scripts/setup.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import scripts.build_dataset as build_dataset  # noqa: E402
import scripts.build_index as build_index  # noqa: E402


def main() -> None:
    print("=== Step 1/2: Fetching movies from TMDB ===")
    build_dataset.main()

    print("\n=== Step 2/2: Building semantic search index ===")
    build_index.main()

    print("\nSetup complete. Run `python run.py` to start the app.")


if __name__ == "__main__":
    main()
