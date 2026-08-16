from __future__ import annotations
import json
from typing import Generator

import requests
from flask import current_app

from app.models import Movie, TasteProfile


class LLMUnavailableError(Exception):
    """Raised when Ollama isn't running or the configured model isn't pulled."""


class FilmRAG:
    """
    Local LLM film recommendation chat, backed by Ollama.

    - Talks to a local Ollama server (OLLAMA_HOST) running OLLAMA_MODEL
      (default: llama3.2:3b) — no manual model file download required,
      just `ollama pull llama3.2:3b`.
    - Streaming: chat() yields tokens one-by-one from Ollama's /api/chat.
    - Conversation memory: last 2 turns are included in every prompt.
    - Taste-aware: if a TasteProfile is supplied, top-rated films are injected
      into the system prompt so the LLM knows the user's preferences.
    - Raises LLMUnavailableError with setup instructions when Ollama can't
      be reached or the model isn't pulled.
    """

    _STOP_TOKENS = ["[INST]", "</s>", "User:", "Human:"]

    def __init__(self, taste_profile: TasteProfile | None = None):
        self.taste_profile = taste_profile
        self._history: list[tuple[str, str]] = []  # [(user, assistant), ...]

    # ── Ollama call ────────────────────────────────────────────────────────────

    @staticmethod
    def _unavailable(detail: str) -> LLMUnavailableError:
        return LLMUnavailableError(
            f"Local LLM not available: {detail}\n"
            "Install Ollama from https://ollama.com, then run:\n"
            "  ollama pull llama3.2:3b\n"
            "Make sure `ollama serve` is running before chatting."
        )

    def _stream_ollama(self, prompt: str, max_tokens: int) -> Generator[str, None, None]:
        host = current_app.config.get("OLLAMA_HOST", "http://localhost:11434")
        model = current_app.config.get("OLLAMA_MODEL", "llama3.2:3b")

        try:
            resp = requests.post(
                f"{host.rstrip('/')}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                    "options": {"num_predict": max_tokens, "stop": self._STOP_TOKENS},
                },
                stream=True,
                timeout=60,
            )
        except requests.exceptions.ConnectionError:
            raise self._unavailable(f"couldn't connect to Ollama at {host}")

        if resp.status_code != 200:
            raise self._unavailable(
                f"Ollama returned {resp.status_code} for model '{model}' — is it pulled?"
            )

        for line in resp.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield token
            if chunk.get("done"):
                break

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

        max_tokens = current_app.config.get("LOCAL_MODEL_MAX_TOKENS", 512)
        full_response = ""

        for token in self._stream_ollama(prompt, max_tokens):
            full_response += token
            yield token

        # Store this turn in conversation history
        self._history.append((message, full_response.strip()))
        # Keep only the last 5 turns to bound memory usage
        self._history = self._history[-5:]
