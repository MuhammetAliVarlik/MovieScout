from flask import Blueprint, current_app, jsonify, render_template, request, session

from app.services import MovieRecommendationEngine, MovieSearchService

home_bp = Blueprint(
    "home_bp", __name__, template_folder="templates",
    static_folder="static", static_url_path="/home/static",
)


def _get_engine() -> MovieRecommendationEngine:
    return current_app.extensions["recommendation_engine"]


@home_bp.route("/")
def home():
    engine = _get_engine()
    genres = sorted({
        g.strip()
        for cell in engine.df["genres"].dropna()
        for g in str(cell).split(",")
        if g.strip()
    })
    return render_template("index.html", genres=genres)


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

    genre = request.form.get("genre", "").strip() or None
    min_rating_raw = request.form.get("min_rating", "").strip()
    min_rating = float(min_rating_raw) if min_rating_raw else None

    recommendations = engine.get_recommendations(
        movie_list, exclude_titles=exclude, limit=limit, genre=genre, min_rating=min_rating
    )
    session["recommendations"] = [r.model_dump() for r in recommendations]
    session["total_similar_movies"] = len(recommendations)
    return jsonify({"status": "success", "total": len(recommendations)})
