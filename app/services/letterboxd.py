from __future__ import annotations
import io
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from collections import Counter
from pathlib import Path

import pandas as pd
import requests
from flask import current_app

from app.models import RatedMovie, TasteProfile

_TMDB_LOOKUP_WORKERS = 8


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
        self._by_title: dict[str, list[int]] = {}
        if dataset_path and Path(dataset_path).exists():
            self._tmdb_df = pd.read_csv(dataset_path)
            self._tmdb_df["title_lower"] = self._tmdb_df["title"].str.lower().str.strip()
            self._tmdb_df["year"] = (
                self._tmdb_df["release_date"]
                .astype(str)
                .str[:4]
                .apply(lambda x: int(x) if x.isdigit() else None)
            )
            # Index title -> row positions once, so per-film lookups are O(1)
            # instead of scanning the whole dataset for every imported film.
            for pos, t in enumerate(self._tmdb_df["title_lower"]):
                self._by_title.setdefault(t, []).append(pos)

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

        # Pass 1: parse each row and try the (fast, O(1)) local lookup. Rows that
        # miss locally are queued for the TMDB API instead of being looked up
        # one at a time — the film-count-sized DataFrame scan and sequential
        # network calls this replaces made a real Letterboxd export (hundreds
        # of films) take tens of seconds to minutes.
        rows: list[dict] = []
        pending_lookup: list[int] = []  # indices into `rows` needing the TMDB API
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

            enriched = self._lookup_local(title, year)
            entry = {"title": title, "year": year, "rating": rating, "watched": watched, "enriched": enriched}
            if enriched is None:
                pending_lookup.append(len(rows))
            rows.append(entry)

        # Pass 2: resolve local misses via the live TMDB API, in parallel — only
        # if a key is configured; otherwise each just falls back to bare title.
        if pending_lookup and current_app.config.get("TMDB_API_KEY"):
            app_obj = current_app._get_current_object()

            def resolve(i: int):
                with app_obj.app_context():
                    entry = rows[i]
                    return i, self._lookup_tmdb_api(entry["title"], entry["year"])

            with ThreadPoolExecutor(max_workers=_TMDB_LOOKUP_WORKERS) as pool:
                for i, live in pool.map(resolve, pending_lookup):
                    if live:
                        rows[i]["enriched"] = live

        films = [
            RatedMovie(
                **(entry["enriched"] or {"title": entry["title"]}),
                user_rating=entry["rating"],
                watched_date=entry["watched"],
            )
            for entry in rows
        ]

        return TasteProfile(films=films)

    # ── Enrichment ─────────────────────────────────────────────────────────────

    def _lookup_local(self, title: str, year: int | None) -> dict | None:
        if self._tmdb_df is None:
            return None
        positions = self._by_title.get(title.lower().strip())
        if not positions:
            return None
        if year is not None:
            year_matches = [p for p in positions if self._tmdb_df["year"].iat[p] == year]
            if year_matches:
                positions = year_matches
        r = self._tmdb_df.iloc[positions[0]]
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
