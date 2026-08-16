from flask import Blueprint, render_template, request, jsonify, session, current_app
from app.services import MovieRecommendationEngine, MovieSearchService

home_bp = Blueprint(
    "home_bp", __name__, template_folder="templates", static_folder="static"
)


def _get_engine() -> MovieRecommendationEngine:
    return current_app.extensions["recommendation_engine"]


@home_bp.route("/")
def home():
    return render_template("index.html")


@home_bp.route("/search_movies", methods=["POST"])
def search_movies():
    query = request.form.get("movieName", "").strip()
    if not query:
        return jsonify([])
    engine = _get_engine()
    service = MovieSearchService(engine)
    results = service.search_movies(query)
    return jsonify([m.model_dump() for m in results])


@home_bp.route("/find_similar_movies", methods=["POST"])
def find_similar_movies():
    movie_list = request.form.getlist("movies[]")
    if not movie_list:
        return jsonify({"status": "error", "message": "No movies selected"}), 400

    engine = _get_engine()
    limit = current_app.config.get("MAX_RECOMMENDATIONS", 20)

    # Exclude films the user has already seen (if a taste profile is in session)
    profile_data = session.get("taste_profile")
    exclude: set[str] = set()
    if profile_data:
        exclude = {f["title"].lower() for f in profile_data.get("films", []) if f.get("title")}

    recommendations = engine.get_recommendations(movie_list, exclude_titles=exclude, limit=limit)
    session["recommendations"] = [r.model_dump() for r in recommendations]
    session["total_similar_movies"] = len(recommendations)
    return jsonify({"status": "success", "total": len(recommendations)})
