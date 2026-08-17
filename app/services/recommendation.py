import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from app.models import Movie

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

STALE_AFTER = timedelta(days=int(5.5 * 30))  # ~5.5 months, safely under TMDB's 6-month cache limit


class MovieRecommendationEngine:
    def __init__(
        self,
        csv_file_path: str | None = None,
        persist_path: str | None = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        require_populated: bool = True,
    ):
        self.csv_file_path = csv_file_path or os.path.join(
            CURRENT_DIR, "..", "..", "data", "processed", "TMDB.csv"
        )
        self.persist_path = persist_path or os.path.join(
            CURRENT_DIR, "..", "..", "data", "chroma"
        )
        self.embedding_model = embedding_model

        self.df: pd.DataFrame | None = None
        self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
        )

        self._load_csv()
        self._check_freshness()
        self._load_or_create_chroma(require_populated=require_populated)

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_csv(self) -> None:
        if not os.path.exists(self.csv_file_path):
            raise RuntimeError(
                f"No movie dataset found at {self.csv_file_path!r}.\n"
                "MovieScout no longer ships a bundled dataset (TMDB's terms don't allow "
                "redistributing their data) — fetch your own with:\n\n"
                "    python scripts/build_dataset.py\n\n"
                "(requires a free TMDB_API_KEY in .env — see themoviedb.org/settings/api)"
            )
        self.df = pd.read_csv(self.csv_file_path)
        self.df["genres"] = self.df["genres"].fillna("")
        print("CSV loaded.")

    def _check_freshness(self) -> None:
        """Warn (don't block) if the dataset is approaching TMDB's 6-month cache limit."""
        meta_path = Path(self.csv_file_path).parent.parent / ".fetch_meta.json"
        if not meta_path.exists():
            return
        try:
            meta = json.loads(meta_path.read_text())
            fetched_at = datetime.fromisoformat(meta["fetched_at"])
        except (json.JSONDecodeError, KeyError, ValueError):
            return
        age = datetime.now(timezone.utc) - fetched_at
        if age > STALE_AFTER:
            print(
                f"[WARNING] Local dataset was fetched {age.days} days ago, approaching "
                "TMDB's 6-month cache limit. Consider re-running "
                "`python scripts/build_dataset.py` to refresh it."
            )

    def _load_or_create_chroma(self, require_populated: bool = True) -> None:
        os.makedirs(self.persist_path, exist_ok=True)
        client = chromadb.PersistentClient(path=self.persist_path)
        self.collection = client.get_or_create_collection(
            name="movies",
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )
        if self.collection.count() == 0:
            if require_populated:
                raise RuntimeError(
                    "The semantic search index is empty. Build it with:\n\n"
                    "    python scripts/build_index.py\n\n"
                    "(run this once after fetching the dataset with scripts/build_dataset.py)"
                )
            return
        print(f"ChromaDB collection loaded ({self.collection.count()} docs).")

    def populate(self, batch_size: int = 500, show_progress: bool = False) -> None:
        """Embed every movie's combined text into ChromaDB. Safe to re-run (upserts)."""
        assert self.df is not None
        docs, ids, metadatas = [], [], []
        for _, row in self.df.iterrows():
            combined = f"{row.get('title', '')} {row.get('overview', '')} {row.get('genres', '')}"
            movie_id = str(row.get("id", row.name))
            docs.append(combined)
            ids.append(movie_id)
            metadatas.append({"title": str(row.get("title", ""))})

        progress = None
        if show_progress:
            from tqdm import tqdm

            progress = tqdm(total=len(docs), desc="Embedding movies", unit="movie")

        for i in range(0, len(docs), batch_size):
            self.collection.upsert(
                documents=docs[i : i + batch_size],
                ids=ids[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )
            if progress is not None:
                progress.update(min(batch_size, len(docs) - i))

        if progress is not None:
            progress.close()

    # ── Public API ────────────────────────────────────────────────────────────

    def lookup_by_chroma_id(self, chroma_id: str) -> pd.Series | None:
        """
        Resolve a ChromaDB document id back to its row in self.df.

        populate() ids each document with row["id"] when the dataset
        has a real "id" column, falling back to the DataFrame's row index
        otherwise (the shipped TMDB.csv has no "id" column, so ids are the
        row index). Mirror that same fallback here so lookups always match.
        """
        assert self.df is not None
        if "id" in self.df.columns:
            matches = self.df[self.df["id"].astype(str) == chroma_id]
            if not matches.empty:
                return matches.iloc[0]
            return None
        try:
            row_idx = int(chroma_id)
        except ValueError:
            return None
        if row_idx not in self.df.index:
            return None
        return self.df.loc[row_idx]

    def get_recommendations(
        self,
        movie_titles: list[str],
        exclude_titles: set[str] | None = None,
        limit: int = 20,
        genre: str | None = None,
        min_rating: float | None = None,
    ) -> list[Movie]:
        assert self.df is not None
        if not movie_titles:
            return []

        # Build query text from the selected movies' overviews + genres
        query_parts = []
        for title in movie_titles:
            row = self.df[self.df["title"] == title]
            if not row.empty:
                r = row.iloc[0]
                query_parts.append(
                    f"{r.get('title', '')} {r.get('overview', '')} {r.get('genres', '')}"
                )

        if not query_parts:
            return []

        query_text = " ".join(query_parts)
        excluded = {t.lower() for t in (exclude_titles or set())} | {
            t.lower() for t in movie_titles
        }

        # Query more than needed so we can filter after — genre/rating filters
        # can eliminate a lot of candidates, so pull a wider pool when active.
        pool_multiplier = 10 if (genre or min_rating) else 3
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(limit * pool_multiplier, self.collection.count()),
        )

        returned_ids = results["ids"][0]
        seen: set[str] = set()
        movies: list[Movie] = []

        for chroma_id in returned_ids:
            r = self.lookup_by_chroma_id(chroma_id)
            if r is None:
                continue
            title = str(r.get("title", ""))
            if title.lower() in excluded or title.lower() in seen:
                continue
            if genre and genre.lower() not in str(r.get("genres", "")).lower():
                continue
            if min_rating and float(r.get("vote_average", 0) or 0) < min_rating:
                continue
            seen.add(title.lower())

            idx = results["ids"][0].index(chroma_id)
            distance = results["distances"][0][idx] if results.get("distances") else 0.0
            score = round(1.0 - distance, 4)

            movies.append(
                Movie(
                    tmdb_id=int(r["id"]) if pd.notna(r.get("id")) else None,
                    title=title,
                    overview=str(r.get("overview", "")),
                    poster_path=r.get("poster_path") or None,
                    backdrop_path=r.get("backdrop_path") or None,
                    release_date=str(r.get("release_date", "")) or None,
                    runtime=int(r["runtime"]) if pd.notna(r.get("runtime")) else None,
                    genres=str(r.get("genres", "")),
                    vote_average=float(r.get("vote_average", 0)),
                    vote_count=int(r.get("vote_count", 0)),
                    status=r.get("status") or None,
                    similarity_score=score,
                )
            )
            if len(movies) >= limit:
                break

        return movies
