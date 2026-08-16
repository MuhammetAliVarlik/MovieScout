from __future__ import annotations
import io
import zipfile
from datetime import date
from collections import Counter
from pathlib import Path

import pandas as pd
import requests
from flask import current_app

from app.models import RatedMovie, TasteProfile


class LetterboxdImporter:
    """
    Parses a Letterboxd ratings.csv export and enriches each entry with
    metadata from the local TMDB dataset.

    The local TMDB CSV is the primary source — no API key required.
    Falls back to the live TMDB API only when TMDB_API_KEY is set in .env.

    Usage
    -----
    importer = LetterboxdImporter()
    profile = importer.from_csv_bytes(file.read())   # raw bytes of ratings.csv
    # or
    profile = importer.from_zip_bytes(file.read())   # raw bytes of export .zip
    """

    def __init__(self) -> None:
        dataset_path = current_app.config.get("TMDB_DATASET_PATH", "")
        self._tmdb_df: pd.DataFrame | None = None
        if dataset_path and Path(dataset_path).exists():
            self._tmdb_df = pd.read_csv(dataset_path)
            self._tmdb_df["title_lower"] = self._tmdb_df["title"].str.lower().str.strip()
            self._tmdb_df["year"] = (
                self._tmdb_df["release_date"]
                .astype(str)
                .str[:4]
                .apply(lambda x: int(x) if x.isdigit() else None)
            )

    # ── Public entry-points ────────────────────────────────────────────────────

    def from_zip_bytes(self, raw: bytes) -> TasteProfile:
        """Accept the full Letterboxd export ZIP and extract ratings.csv."""
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            csv_name = next(
                (n for n in zf.namelist() if "ratings" in n.lower() and n.endswith(".csv")),
                None,
            )
            if csv_name is None:
                raise ValueError("ratings.csv not found in the uploaded ZIP.")
            csv_bytes = zf.read(csv_name)
        return self.from_csv_bytes(csv_bytes)

    def from_csv_bytes(self, raw: bytes) -> TasteProfile:
        """Parse raw bytes of a Letterboxd ratings.csv."""
        df = pd.read_csv(io.BytesIO(raw))
        return self._parse_dataframe(df)

    def from_csv_path(self, path: str | Path) -> TasteProfile:
        df = pd.read_csv(path)
        return self._parse_dataframe(df)

    # ── Parsing ────────────────────────────────────────────────────────────────

    def _parse_dataframe(self, df: pd.DataFrame) -> TasteProfile:
        # Letterboxd may use 'Name' or 'Title' as the column header
        if "Name" in df.columns and "Title" not in df.columns:
            df = df.rename(columns={"Name": "Title"})

        required = {"Title", "Rating"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"ratings.csv is missing columns: {missing}")

        films: list[RatedMovie] = []
        for _, row in df.iterrows():
            title = str(row["Title"]).strip()
            try:
                rating = float(row["Rating"])
            except (ValueError, TypeError):
                continue  # skip unrated entries

            year = int(row["Year"]) if "Year" in df.columns and pd.notna(row.get("Year")) else None
            watched_raw = row.get("Watched Date")
            watched: date | None = None
            if pd.notna(watched_raw):
                try:
                    watched = date.fromisoformat(str(watched_raw))
                except ValueError:
                    pass

            enriched = self._enrich(title, year)
            films.append(
                RatedMovie(
                    **enriched,
                    user_rating=rating,
                    watched_date=watched,
                )
            )

        return TasteProfile(films=films)

    # ── Enrichment ─────────────────────────────────────────────────────────────

    def _enrich(self, title: str, year: int | None) -> dict:
        """Return a dict of Movie fields. Tries local dataset first, then live API."""
        local = self._lookup_local(title, year)
        if local:
            return local
        if current_app.config.get("TMDB_API_KEY"):
            live = self._lookup_tmdb_api(title, year)
            if live:
                return live
        return {"title": title}

    def _lookup_local(self, title: str, year: int | None) -> dict | None:
        if self._tmdb_df is None:
            return None
        candidates = self._tmdb_df[self._tmdb_df["title_lower"] == title.lower().strip()]
        if year is not None:
            year_match = candidates[candidates["year"] == year]
            if not year_match.empty:
                candidates = year_match
        if candidates.empty:
            return None
        r = candidates.iloc[0]
        return self._row_to_dict(r)

    def _lookup_tmdb_api(self, title: str, year: int | None) -> dict | None:
        key = current_app.config["TMDB_API_KEY"]
        params: dict = {"api_key": key, "query": title, "language": "en-US", "page": 1}
        if year:
            params["primary_release_year"] = year
        try:
            resp = requests.get(
                "https://api.themoviedb.org/3/search/movie",
                params=params,
                timeout=5,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
        except Exception:
            return None
        if not results:
            return None
        m = results[0]
        return {
            "tmdb_id": m.get("id"),
            "title": m.get("title", title),
            "overview": m.get("overview", ""),
            "poster_path": m.get("poster_path"),
            "backdrop_path": m.get("backdrop_path"),
            "release_date": m.get("release_date") or None,
            "genres": "",
            "vote_average": float(m.get("vote_average", 0)),
            "vote_count": int(m.get("vote_count", 0)),
        }

    @staticmethod
    def _row_to_dict(r) -> dict:
        import pandas as _pd
        return {
            "tmdb_id": int(r["id"]) if _pd.notna(r.get("id")) else None,
            "title": str(r.get("title", "")),
            "overview": str(r.get("overview", "")),
            "poster_path": r.get("poster_path") or None,
            "backdrop_path": r.get("backdrop_path") or None,
            "release_date": str(r.get("release_date", "")) or None,
            "runtime": int(r["runtime"]) if _pd.notna(r.get("runtime")) else None,
            "genres": str(r.get("genres", "")),
            "vote_average": float(r.get("vote_average", 0)),
            "vote_count": int(r.get("vote_count", 0)),
            "status": r.get("status") or None,
        }

    # ── Profile summary ────────────────────────────────────────────────────────

    @staticmethod
    def summarise(profile: TasteProfile) -> dict:
        """Return a summary dict suitable for JSON serialisation."""
        all_genres: list[str] = []
        decades: list[int] = []
        for f in profile.films:
            if f.genres:
                for g in str(f.genres).split(","):
                    g = g.strip()
                    if g:
                        all_genres.append(g)
            if f.release_date:
                try:
                    yr = int(str(f.release_date)[:4])
                    decades.append((yr // 10) * 10)
                except ValueError:
                    pass

        top_genres = [g for g, _ in Counter(all_genres).most_common(5)]
        top_decades = [d for d, _ in Counter(decades).most_common(3)]
        top_films = [
            {"title": f.title, "rating": f.user_rating}
            for f in profile.top_films[:5]
        ]

        return {
            "total_films": len(profile.films),
            "top_genres": top_genres,
            "top_decades": top_decades,
            "top_films": top_films,
        }
