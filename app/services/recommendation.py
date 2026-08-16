import os
import pickle
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from sklearn.metrics.pairwise import cosine_similarity
from app.models import Movie

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class MovieRecommendationEngine:
    def __init__(
        self,
        csv_file_path: str | None = None,
        persist_path: str | None = None,
        embedding_model: str = "all-MiniLM-L6-v2",
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
        self._load_or_create_chroma()

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_csv(self) -> None:
        self.df = pd.read_csv(self.csv_file_path)
        self.df["genres"] = self.df["genres"].fillna("")
        print("CSV loaded.")

    def _load_or_create_chroma(self) -> None:
        os.makedirs(self.persist_path, exist_ok=True)
        client = chromadb.PersistentClient(path=self.persist_path)
        self.collection = client.get_or_create_collection(
            name="movies",
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )
        if self.collection.count() == 0:
            self._populate_chroma()
            print("ChromaDB collection created and populated.")
        else:
            print(f"ChromaDB collection loaded ({self.collection.count()} docs).")

    def _populate_chroma(self) -> None:
        """Index every movie's combined text into ChromaDB."""
        assert self.df is not None
        docs, ids, metadatas = [], [], []
        for _, row in self.df.iterrows():
            combined = f"{row.get('title', '')} {row.get('overview', '')} {row.get('genres', '')}"
            movie_id = str(row.get("id", row.name))
            docs.append(combined)
            ids.append(movie_id)
            metadatas.append({"title": str(row.get("title", ""))})

        # ChromaDB has a max batch size of 5461
        batch = 5000
        for i in range(0, len(docs), batch):
            self.collection.add(
                documents=docs[i : i + batch],
                ids=ids[i : i + batch],
                metadatas=metadatas[i : i + batch],
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def lookup_by_chroma_id(self, chroma_id: str) -> pd.Series | None:
        """
        Resolve a ChromaDB document id back to its row in self.df.

        _populate_chroma() ids each document with row["id"] when the dataset
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

        # Query more than needed so we can filter after
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(limit * 3, self.collection.count()),
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
