from flask import (
    Blueprint, render_template, request,
    Response, session, jsonify, current_app,
)
from app.services import FilmRAG, MovieSearchService, LLMUnavailableError
from app.models import TasteProfile

chat_bp = Blueprint(
    "chat_bp", __name__, template_folder="templates", static_folder="static"
)


def _get_rag() -> FilmRAG:
    """Creates a FilmRAG instance with the current session's taste profile."""
    profile_data = session.get("taste_profile")
    taste: TasteProfile | None = None
    if profile_data:
        try:
            taste = TasteProfile.model_validate(profile_data)
        except Exception:
            taste = None
    return FilmRAG(taste_profile=taste)


@chat_bp.route("/chat")
def chat():
    return render_template("chat.html")


@chat_bp.route("/chat/stream", methods=["POST"])
def chat_stream():
    """
    Server-Sent Events endpoint.  The frontend reads this with fetch() +
    ReadableStream; each yielded token is a raw SSE data line.
    """
    message = request.form.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    rag = _get_rag()
    app_obj = current_app._get_current_object()

    def generate():
        # Runs lazily, after the request's app context has already been torn
        # down — re-enter it explicitly so current_app lookups inside
        # rag.chat() (config, the recommendation engine) still work.
        with app_obj.app_context():
            try:
                for token in rag.chat(message):
                    # Escape newlines so each token is a valid SSE data line
                    yield f"data: {token.replace(chr(10), ' ')}\n\n"
                yield "data: [DONE]\n\n"
            except LLMUnavailableError as exc:
                yield f"data: [ERROR] {str(exc).splitlines()[0]}\n\n"
                yield "data: [DONE]\n\n"

    return Response(generate(), mimetype="text/event-stream")


@chat_bp.route("/chat/search", methods=["POST"])
def chat_search():
    """
    Exact-title lookup used by the frontend after the LLM names a film.
    Returns the first match as a JSON Movie object (or null if not found).
    """
    title = request.form.get("title", "").strip()
    if not title:
        return jsonify(None)

    engine = current_app.extensions["recommendation_engine"]
    service = MovieSearchService(engine)
    results = service.search_chat_movies(title, limit=1)
    if results:
        return jsonify(results[0].model_dump())
    return jsonify(None)
