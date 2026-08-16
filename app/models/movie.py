from pydantic import BaseModel
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
    letterboxd_slug: str | None = None


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
