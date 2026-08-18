"""
Fetch a bounded, popularity-ranked subset of movies from the TMDB API and
write it to data/processed/TMDB.csv.

TMDB's API Terms of Use prohibit redistributing their data or caching it
for more than 6 months, so MovieScout no longer ships a bundled dataset —
every user runs this script with their own free TMDB API key instead.
Only the fields the app actually uses are fetched, and only a bounded
top-N subset (never TMDB's full catalog).

Usage:
    python scripts/build_dataset.py
"""

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import time

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import Config

TMDB_NOTE = "This product uses the TMDB API but is not endorsed or certified by TMDB."
API_BASE = "https://api.themoviedb.org/3"
PAGE_SIZE = 20
MAX_REQUESTS_PER_SECOND = 30
MAX_RETRIES = 5

# TMDB's list endpoints (including /discover/movie) hard-cap pagination at
# page 500 regardless of sort/filter — requesting page 501+ returns a 400,
# not more results. That's a ceiling of 500*20 = 10,000 movies for any single
# query, not something a bigger TMDB_BUILD_LIMIT can raise.
TMDB_MAX_PAGE = 500
TMDB_MAX_FETCHABLE = TMDB_MAX_PAGE * PAGE_SIZE


class RateLimiter:
    def __init__(self, max_per_second: float):
        self.min_interval = 1.0 / max_per_second
        self._last_call = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last_call
        remaining = self.min_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_call = time.monotonic()


def _get(session: requests.Session, path: str, params: dict, limiter: RateLimiter) -> dict:
    for attempt in range(MAX_RETRIES):
        limiter.wait()
        resp = session.get(f"{API_BASE}{path}", params=params, timeout=15)
        if resp.status_code == 429:
            backoff = 2**attempt
            print(f"  Rate limited by TMDB, backing off {backoff}s...")
            time.sleep(backoff)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"Gave up on {path} after {MAX_RETRIES} retries (persistent 429s)")


def fetch_genre_map(session: requests.Session, api_key: str, limiter: RateLimiter) -> dict[int, str]:
    data = _get(session, "/genre/movie/list", {"api_key": api_key, "language": "en-US"}, limiter)
    return {g["id"]: g["name"] for g in data.get("genres", [])}


class _PartialFetchError(Exception):
    """Raised when a page fetch fails partway through — carries whatever was
    already fetched (in .args[0]) so the caller can still write it out."""


def fetch_movies(session: requests.Session, api_key: str, limit: int, limiter: RateLimiter) -> list[dict]:
    genre_map = fetch_genre_map(session, api_key, limiter)
    total_pages = min(math.ceil(limit / PAGE_SIZE), TMDB_MAX_PAGE)
    movies: list[dict] = []
    seen_ids: set[int] = set()

    for page in range(1, total_pages + 1):
        try:
            data = _get(
                session,
                "/discover/movie",
                {
                    "api_key": api_key,
                    "language": "en-US",
                    "sort_by": "popularity.desc",
                    "include_adult": "false",
                    "page": page,
                },
                limiter,
            )
        except Exception as exc:
            raise _PartialFetchError(movies) from exc
        results = data.get("results", [])
        if not results:
            break

        for m in results:
            if m["id"] in seen_ids:
                continue
            seen_ids.add(m["id"])
            movies.append(
                {
                    "id": m.get("id"),
                    "title": m.get("title", ""),
                    "overview": m.get("overview", ""),
                    "genres": ", ".join(
                        genre_map.get(gid, "") for gid in m.get("genre_ids", []) if gid in genre_map
                    ),
                    "poster_path": m.get("poster_path"),
                    "backdrop_path": m.get("backdrop_path"),
                    "release_date": m.get("release_date"),
                    "vote_average": m.get("vote_average", 0),
                    "vote_count": m.get("vote_count", 0),
                }
            )
            if len(movies) >= limit:
                break

        if page % 25 == 0 or page == total_pages:
            print(f"  Fetched page {page}/{total_pages} ({len(movies)}/{limit} movies)")

        if len(movies) >= limit or page >= data.get("total_pages", total_pages):
            break

    return movies


def main() -> None:
    cfg = Config()
    if not cfg.TMDB_API_KEY:
        raise SystemExit(
            "TMDB_API_KEY is not set.\n\n"
            "Get a free key at https://www.themoviedb.org/settings/api "
            "(no approval needed for non-commercial use), then add it to your .env file:\n\n"
            "    TMDB_API_KEY=your-key-here\n"
        )

    limit = cfg.TMDB_BUILD_LIMIT
    if limit > TMDB_MAX_FETCHABLE:
        print(
            f"[WARNING] TMDB_BUILD_LIMIT={limit}, but TMDB's /discover/movie "
            f"pagination hard-caps at {TMDB_MAX_FETCHABLE} results (page 500) "
            f"for any single sort order — fetching {TMDB_MAX_FETCHABLE} instead."
        )
        limit = TMDB_MAX_FETCHABLE
    print(f"Fetching the top {limit} popular movies from TMDB...")

    session = requests.Session()
    limiter = RateLimiter(MAX_REQUESTS_PER_SECOND)
    try:
        movies = fetch_movies(session, cfg.TMDB_API_KEY, limit, limiter)
    except Exception as exc:  # noqa: BLE001
        # Don't let a late failure (a bad page, a network drop) throw away
        # several minutes of already-fetched pages — write what we have.
        print(f"\n[WARNING] Fetch stopped early ({exc!r}). Writing partial results so far.")
        movies = exc.args[0] if isinstance(exc, _PartialFetchError) else []

    csv_path = Path(cfg.TMDB_DATASET_PATH)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(movies).to_csv(csv_path, index=False)

    meta_path = csv_path.parent.parent / ".fetch_meta.json"
    meta_path.write_text(
        json.dumps(
            {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "row_count": len(movies),
                "tmdb_note": TMDB_NOTE,
            },
            indent=2,
        )
    )

    print(f"\nWrote {len(movies)} movies to {csv_path}")
    print(f"Wrote fetch metadata to {meta_path}")


if __name__ == "__main__":
    main()
