import re

from pydantic import BaseModel, computed_field
from datetime import date


class Movie(BaseModel):
    tmdb_id: int | None = None
    title: str = ""
    overview: str = ""
    poster_path: str | None = None
    backdrop_path: str | None = None
    release_date: str | None = None
    runtime: int | None = None
    genres: str = ""
    vote_average: float = 0.0
    vote_count: int = 0
    status: str | None = None
    similarity_score: float | None = None

    @computed_field
    @property
    def letterboxd_url(self) -> str:
        # Best-effort guess at the real Letterboxd slug — Letterboxd has no
        # public lookup API, so this is the same title-to-slug convention
        # Letterboxd itself uses, not a verified match.
        slug = re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")
        year = (self.release_date or "")[:4]
        if year.isdigit():
            return f"https://letterboxd.com/film/{slug}-{year}/"
        return f"https://letterboxd.com/film/{slug}/"


class RatedMovie(Movie):
    user_rating: float  # 0.5–5.0 on the Letterboxd half-star scale
    watched_date: date | None = None


class TasteProfile(BaseModel):
    films: list[RatedMovie] = []

    @property
    def watched_titles(self) -> set[str]:
        return {f.title.lower() for f in self.films}

    @property
    def top_films(self) -> list[RatedMovie]:
        return sorted(self.films, key=lambda f: f.user_rating, reverse=True)[:10]
