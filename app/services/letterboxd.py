from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import io
from pathlib import Path
import re
import zipfile

from defusedxml import ElementTree as SafeET
from flask import current_app
import pandas as pd
import requests

from app.extensions import cache
from app.models import RatedMovie, TasteProfile

_TMDB_LOOKUP_WORKERS = 8

_TMDB_LOOKUP_CACHE_TTL = 60 * 60 * 24  # 24h — movie metadata barely changes day to day
_TMDB_LOOKUP_MISS = "__TMDB_LOOKUP_MISS__"  # cached marker for "looked up, no result"

# Letterboxd usernames are alphanumeric + underscores only (checked against
# real accounts) — validating this means the RSS URL below is always built
# from a known-safe host + slug, never anything an attacker could redirect
# elsewhere or use to smuggle path segments.
_LETTERBOXD_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{1,40}$")
_RSS_TIMEOUT = 10
_RSS_MAX_BYTES = 5 * 1024 * 1024  # a diary feed is a few hundred KB — 5MB is generous headroom
_MAX_UNCOMPRESSED_CSV_BYTES = 100 * 1024 * 1024  # even a huge ratings.csv is a few MB

_LB_NS = "https://letterboxd.com"
_TMDB_NS = "https://themoviedb.org"


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
        self._by_id: dict[int, int] = {}
        if dataset_path and Path(dataset_path).exists():
            self._tmdb_df = pd.read_csv(dataset_path)
            # Missing overview/genres land as NaN — left alone, str(nan) renders
            # as the literal text "nan" wherever these are shown or joined.
            self._tmdb_df["overview"] = self._tmdb_df["overview"].fillna("")
            self._tmdb_df["genres"] = self._tmdb_df["genres"].fillna("")
            self._tmdb_df["title_lower"] = self._tmdb_df["title"].str.lower().str.strip()
            # pd.notna() check first, not .astype(str) then .isdigit() — whether
            # NaN survives an astype(str) cast as a real string "nan" or stays a
            # float depends on the pandas version (confirmed different between
            # pandas 2.x and 3.x), so isdigit() on the result isn't reliable.
            self._tmdb_df["year"] = self._tmdb_df["release_date"].apply(
                lambda x: int(str(x)[:4]) if pd.notna(x) and str(x)[:4].isdigit() else None
            )
            # Index title -> row positions once, so per-film lookups are O(1)
            # instead of scanning the whole dataset for every imported film.
            for pos, t in enumerate(self._tmdb_df["title_lower"]):
                self._by_title.setdefault(t, []).append(pos)
            if "id" in self._tmdb_df.columns:
                for pos, tid in enumerate(self._tmdb_df["id"]):
                    if pd.notna(tid):
                        self._by_id[int(tid)] = pos

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
            # The upload itself is size-capped (MAX_CONTENT_LENGTH), but a
            # zip can still decompress to far more than its compressed size
            # ("zip bomb") — check the claimed decompressed size before
            # reading it fully into memory. zipfile.getinfo().file_size comes
            # from the archive's own metadata, not a real read, so this is a
            # cheap guard, not a guarantee — good enough for a single-user
            # portfolio app, not a substitute for real quota/sandboxing.
            info = zf.getinfo(csv_name)
            if info.file_size > _MAX_UNCOMPRESSED_CSV_BYTES:
                raise ValueError("That ratings.csv is unexpectedly large — aborting.")
            csv_bytes = zf.read(csv_name)
        return self.from_csv_bytes(csv_bytes)

    def from_csv_bytes(self, raw: bytes) -> TasteProfile:
        """Parse raw bytes of a Letterboxd ratings.csv."""
        df = pd.read_csv(io.BytesIO(raw))
        return self._parse_dataframe(df)

    def from_csv_path(self, path: str | Path) -> TasteProfile:
        df = pd.read_csv(path)
        return self._parse_dataframe(df)

    def from_rss_username(self, username: str) -> TasteProfile:
        """
        Fetch a Letterboxd user's public diary RSS feed (letterboxd.com/<user>/rss/)
        and build a TasteProfile from their recently watched, rated films.

        Lighter-weight than the full ratings.csv export: no file to download
        and re-upload, but Letterboxd's diary RSS only carries recent entries
        (not full history), same as the feed you'd see in an RSS reader.
        """
        username = username.strip().lstrip("@")
        if not _LETTERBOXD_USERNAME_RE.match(username):
            raise ValueError(
                "That doesn't look like a valid Letterboxd username "
                "(letters, numbers, and underscores only)."
            )

        url = f"https://letterboxd.com/{username}/rss/"
        try:
            resp = requests.get(
                url,
                timeout=_RSS_TIMEOUT,
                headers={"User-Agent": "MovieScout/1.0 (+https://github.com/MuhammetAliVarlik/MovieScout)"},
                stream=True,
            )
            resp.raise_for_status()
            raw = resp.raw.read(_RSS_MAX_BYTES + 1, decode_content=True)
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                raise ValueError(f"No public Letterboxd profile found for {username!r}.") from exc
            raise ValueError(f"Couldn't reach Letterboxd right now ({exc}).") from exc
        except requests.exceptions.RequestException as exc:
            raise ValueError(f"Couldn't reach Letterboxd right now ({exc}).") from exc

        if len(raw) > _RSS_MAX_BYTES:
            raise ValueError("That RSS feed came back unexpectedly large — aborting.")

        try:
            root = SafeET.fromstring(raw)
        except Exception as exc:
            raise ValueError("That didn't look like a valid RSS feed.") from exc

        rows: list[dict] = []
        pending_lookup: list[int] = []
        for item in root.iter("item"):
            title_el = item.find(f"{{{_LB_NS}}}filmTitle")
            if title_el is None or not (title_el.text or "").strip():
                continue  # not a film-watch entry (e.g. a list update)
            title = title_el.text.strip()

            rating_el = item.find(f"{{{_LB_NS}}}memberRating")
            if rating_el is None or not (rating_el.text or "").strip():
                continue  # unrated — skip, same as the CSV import path
            try:
                rating = float(rating_el.text)
            except ValueError:
                continue

            year_el = item.find(f"{{{_LB_NS}}}filmYear")
            year = int(year_el.text) if year_el is not None and (year_el.text or "").isdigit() else None

            watched_el = item.find(f"{{{_LB_NS}}}watchedDate")
            watched: date | None = None
            if watched_el is not None and (watched_el.text or "").strip():
                try:
                    watched = date.fromisoformat(watched_el.text.strip())
                except ValueError:
                    pass

            # Letterboxd's RSS includes the TMDB id directly for most films —
            # a direct id lookup is far more reliable than title/year matching.
            tmdb_id_el = item.find(f"{{{_TMDB_NS}}}movieId")
            enriched = None
            if tmdb_id_el is not None and (tmdb_id_el.text or "").isdigit():
                enriched = self._lookup_local_by_id(int(tmdb_id_el.text))
            if enriched is None:
                enriched = self._lookup_local(title, year)

            entry = {"title": title, "year": year, "rating": rating, "watched": watched, "enriched": enriched}
            if enriched is None:
                pending_lookup.append(len(rows))
            rows.append(entry)

        self._resolve_pending_via_tmdb(rows, pending_lookup)

        films = [
            RatedMovie(
                **(entry["enriched"] or {"title": entry["title"]}),
                user_rating=entry["rating"],
                watched_date=entry["watched"],
            )
            for entry in rows
        ]
        return TasteProfile(films=films)

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
        self._resolve_pending_via_tmdb(rows, pending_lookup)

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

    def _lookup_local_by_id(self, tmdb_id: int) -> dict | None:
        if self._tmdb_df is None:
            return None
        pos = self._by_id.get(tmdb_id)
        if pos is None:
            return None
        return self._row_to_dict(self._tmdb_df.iloc[pos])

    def _resolve_pending_via_tmdb(self, rows: list[dict], pending: list[int]) -> None:
        """Fill in `rows[i]["enriched"]` for each index in `pending` via the
        live TMDB API, in parallel — only if a key is configured."""
        if not pending or not current_app.config.get("TMDB_API_KEY"):
            return
        app_obj = current_app._get_current_object()

        def resolve(i: int):
            with app_obj.app_context():
                entry = rows[i]
                return i, self._lookup_tmdb_api(entry["title"], entry["year"])

        with ThreadPoolExecutor(max_workers=_TMDB_LOOKUP_WORKERS) as pool:
            for i, live in pool.map(resolve, pending):
                if live:
                    rows[i]["enriched"] = live

    def _lookup_tmdb_api(self, title: str, year: int | None) -> dict | None:
        cache_key = f"tmdb_api_lookup:{title.strip().lower()}:{year or ''}"
        cached = cache.get(cache_key)
        if cached is not None:
            return None if cached == _TMDB_LOOKUP_MISS else cached

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
        except Exception:  # noqa: BLE001 — any failure here (timeout, bad JSON, ...) should
            return None  # degrade to "no match" rather than break the whole import
        if not results:
            cache.set(cache_key, _TMDB_LOOKUP_MISS, timeout=_TMDB_LOOKUP_CACHE_TTL)
            return None
        m = results[0]
        result = {
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
        cache.set(cache_key, result, timeout=_TMDB_LOOKUP_CACHE_TTL)
        return result

    @staticmethod
    def _row_to_dict(r) -> dict:
        import pandas as _pd
        return {
            "tmdb_id": int(r["id"]) if _pd.notna(r.get("id")) else None,
            "title": str(r.get("title", "")),
            "overview": str(r.get("overview", "")),
            "poster_path": r.get("poster_path") if _pd.notna(r.get("poster_path")) else None,
            "backdrop_path": r.get("backdrop_path") if _pd.notna(r.get("backdrop_path")) else None,
            "release_date": str(r.get("release_date")) if _pd.notna(r.get("release_date")) else None,
            "runtime": int(r["runtime"]) if _pd.notna(r.get("runtime")) else None,
            "genres": str(r.get("genres", "")),
            "vote_average": float(r.get("vote_average", 0)),
            "vote_count": int(r.get("vote_count", 0)),
            "status": r.get("status") if _pd.notna(r.get("status")) else None,
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
