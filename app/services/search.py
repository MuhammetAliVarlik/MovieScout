from __future__ import annotations

from app.extensions import cache
from app.models import Movie
from app.services.recommendation import MovieRecommendationEngine

_SEARCH_COLS = [
    "title", "vote_average", "vote_count", "status",
    "release_date", "runtime", "overview", "poster_path",
    "genres", "backdrop_path",
]


class MovieSearchService:
    def __init__(self, engine: MovieRecommendationEngine):
        self.engine = engine

    def search_movies(self, query: str, limit: int = 10) -> list[Movie]:
        """Case-insensitive substring search — used for the search autocomplete."""
        df = self.engine.df
        if df is None or not query:
            return []
        cache_key = f"search:{query.strip().lower()}:{limit}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        mask = df["title"].str.contains(query, case=False, na=False)
        results = self._rows_to_movies(df[mask].head(limit))
        cache.set(cache_key, results)
        return results

    def search_chat_movies(self, query: str, limit: int = 5) -> list[Movie]:
        """Exact-title match — used after the LLM names a specific film."""
        df = self.engine.df
        if df is None or not query:
            return []
        clean = query.strip().lower()
        mask = df["title"].str.strip().str.lower() == clean
        return self._rows_to_movies(df[mask].head(limit))

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _rows_to_movies(rows) -> list[Movie]:
        import pandas as pd

        movies = []
        for _, r in rows.iterrows():
            movies.append(
                Movie(
                    tmdb_id=int(r["id"]) if pd.notna(r.get("id")) else None,
                    title=str(r.get("title", "")),
                    overview=str(r.get("overview", "")),
                    poster_path=r.get("poster_path") if pd.notna(r.get("poster_path")) else None,
                    backdrop_path=r.get("backdrop_path") if pd.notna(r.get("backdrop_path")) else None,
                    release_date=str(r.get("release_date")) if pd.notna(r.get("release_date")) else None,
                    runtime=int(r["runtime"]) if pd.notna(r.get("runtime")) else None,
                    genres=str(r.get("genres", "")),
                    vote_average=float(r.get("vote_average", 0)),
                    vote_count=int(r.get("vote_count", 0)),
                    status=r.get("status") if pd.notna(r.get("status")) else None,
                )
            )
        return movies
