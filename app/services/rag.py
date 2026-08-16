from __future__ import annotations
from pathlib import Path
from typing import Generator

from flask import current_app
from llama_cpp import Llama

from app.models import Movie, TasteProfile


class FilmRAG:
    """
    Local LLM film recommendation chat, backed by llama_cpp_python.

    Improvements over the original MovieRecommendationRAG:
    - Model path is read from app config (LOCAL_MODEL_PATH), not hardcoded.
    - Streaming: chat() yields tokens one-by-one via llama_cpp stream=True.
    - Conversation memory: last 2 turns are included in every prompt.
    - Taste-aware: if a TasteProfile is supplied, top-rated films are injected
      into the system prompt so the LLM knows the user's preferences.
    - Clear FileNotFoundError with download instructions when model is missing.
    - Stop tokens keep the model from rambling past the answer.
    """

    _STOP_TOKENS = ["[INST]", "</s>", "User:", "Human:"]

    def __init__(self, taste_profile: TasteProfile | None = None):
        self.taste_profile = taste_profile
        self._history: list[tuple[str, str]] = []  # [(user, assistant), ...]
        self._llm: Llama | None = None

    # ── LLM lazy init ─────────────────────────────────────────────────────────

    def _get_llm(self) -> Llama:
        if self._llm is not None:
            return self._llm

        model_path = str(current_app.config["LOCAL_MODEL_PATH"])
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Local LLM model not found at: {model_path}\n"
                "Download a free GGUF model and set LOCAL_MODEL_PATH in .env.\n"
                "Example (Mistral 7B, ~4 GB):\n"
                "  python -c \"from huggingface_hub import hf_hub_download; "
                "hf_hub_download(repo_id='TheBloke/Mistral-7B-Instruct-v0.2-GGUF', "
                "filename='mistral-7b-instruct-v0.2.Q4_K_M.gguf', local_dir='./models')\""
            )

        self._llm = Llama(
            model_path=model_path,
            n_ctx=current_app.config.get("LOCAL_MODEL_CONTEXT_LENGTH", 4096),
            n_threads=4,
            n_batch=512,
            verbose=False,
        )
        return self._llm

    # ── Prompt building ────────────────────────────────────────────────────────

    def _build_system_prompt(self, context_films: list[Movie]) -> str:
        taste_section = ""
        if self.taste_profile and self.taste_profile.top_films:
            titles = [f.title for f in self.taste_profile.top_films[:5]]
            taste_section = (
                "\nThe user's top-rated films are: "
                + ", ".join(f'"{t}"' for t in titles)
                + ". Use these tastes to personalise your recommendations."
            )

        context_section = ""
        if context_films:
            snippets = []
            for m in context_films[:10]:
                snippets.append(f'- "{m.title}" ({m.release_date or ""}): {m.overview[:120]}')
            context_section = "\n\nRelevant films from the database:\n" + "\n".join(snippets)

        return (
            "You are CineMatch, an expert film recommendation assistant. "
            "Recommend films thoughtfully, always enclosing film titles in double quotes. "
            "Keep answers concise (3–5 sentences). Do not spoil endings."
            + taste_section
            + context_section
        )

    def _build_prompt(self, user_message: str, context_films: list[Movie]) -> str:
        system = self._build_system_prompt(context_films)

        # Include the last 2 turns of conversation history
        history_block = ""
        for user_turn, assistant_turn in self._history[-2:]:
            history_block += f"[INST] {user_turn} [/INST] {assistant_turn} "

        return f"[INST] <<SYS>>\n{system}\n<</SYS>>\n\n{history_block}{user_message} [/INST]"

    # ── ChromaDB retrieval ─────────────────────────────────────────────────────

    def _retrieve_context(self, query: str) -> list[Movie]:
        """Pull relevant films from ChromaDB using the user's message as the query."""
        try:
            engine = current_app.extensions.get("recommendation_engine")
            if engine is None:
                return []
            n = current_app.config.get("RAG_CONTEXT_FILMS", 10)
            results = engine.collection.query(
                query_texts=[query],
                n_results=min(n, engine.collection.count()),
            )
            films: list[Movie] = []
            for chroma_id in results["ids"][0]:
                import pandas as pd
                row = engine.df[engine.df["id"].astype(str) == chroma_id]
                if not row.empty:
                    r = row.iloc[0]
                    films.append(
                        Movie(
                            tmdb_id=int(r["id"]) if pd.notna(r.get("id")) else None,
                            title=str(r.get("title", "")),
                            overview=str(r.get("overview", "")),
                            release_date=str(r.get("release_date", "")) or None,
                        )
                    )
            return films
        except Exception:
            return []

    # ── Public API ─────────────────────────────────────────────────────────────

    def chat(self, message: str) -> Generator[str, None, None]:
        """Yield response tokens one-by-one (SSE-friendly)."""
        context_films = self._retrieve_context(message)
        prompt = self._build_prompt(message, context_films)
        llm = self._get_llm()

        max_tokens = current_app.config.get("LOCAL_MODEL_MAX_TOKENS", 512)
        full_response = ""

        for chunk in llm(
            prompt,
            max_tokens=max_tokens,
            stop=self._STOP_TOKENS,
            stream=True,
        ):
            token = chunk["choices"][0]["text"]
            full_response += token
            yield token

        # Store this turn in conversation history
        self._history.append((message, full_response.strip()))
        # Keep only the last 5 turns to bound memory usage
        self._history = self._history[-5:]
