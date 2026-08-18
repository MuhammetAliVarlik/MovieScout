from flask import Blueprint, jsonify, request, session

from app.services import LetterboxdImporter

api_bp = Blueprint("api_bp", __name__)


@api_bp.route("/import", methods=["POST"])
def import_letterboxd():
    """
    Accept a Letterboxd export ZIP or a bare ratings.csv.
    Stores the resulting TasteProfile (serialised) in the session.
    Returns a taste profile summary as JSON.
    """
    uploaded = request.files.get("file")
    if uploaded is None:
        return jsonify({"error": "No file uploaded"}), 400

    filename = uploaded.filename or ""
    raw = uploaded.read()

    importer = LetterboxdImporter()
    try:
        if filename.lower().endswith(".zip"):
            profile = importer.from_zip_bytes(raw)
        elif filename.lower().endswith(".csv"):
            profile = importer.from_csv_bytes(raw)
        else:
            return jsonify({"error": "Upload a .zip or .csv file"}), 400
    except ValueError as exc:
        # Our own code raises ValueError with clean, user-facing messages
        # ("ratings.csv not found in the uploaded ZIP.", etc) — safe to show.
        return jsonify({"error": str(exc)}), 422
    except Exception:  # noqa: BLE001 — anything else is unexpected (a corrupt
        # file, a parser edge case); don't leak its raw message to the client.
        return jsonify({"error": "Couldn't parse that file — is it a real Letterboxd export?"}), 422

    # Persist the profile in the session for use by other blueprints
    session["taste_profile"] = profile.model_dump(mode="json")

    return jsonify(LetterboxdImporter.summarise(profile))


@api_bp.route("/import/rss", methods=["POST"])
def import_letterboxd_rss():
    """
    Fetch a Letterboxd user's public diary RSS feed (a lighter-weight
    alternative to uploading a ratings.csv export) and build/store a
    TasteProfile from it, same as /import.
    """
    username = request.form.get("username", "").strip()
    if not username:
        return jsonify({"error": "Enter a Letterboxd username"}), 400

    importer = LetterboxdImporter()
    try:
        profile = importer.from_rss_username(username)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422

    if not profile.films:
        return jsonify({
            "error": "No rated films found in that profile's recent diary "
                     "(private profile, or nothing rated recently)."
        }), 422

    session["taste_profile"] = profile.model_dump(mode="json")
    return jsonify(LetterboxdImporter.summarise(profile))


@api_bp.route("/profile", methods=["GET"])
def get_profile():
    """Return the current session's taste profile summary, or an empty one."""
    profile_data = session.get("taste_profile")
    if not profile_data:
        return jsonify({"total_films": 0, "top_genres": [], "top_decades": [], "top_films": []})

    from app.models import TasteProfile
    try:
        profile = TasteProfile.model_validate(profile_data)
    except Exception:  # noqa: BLE001 — any validation failure means the same thing here
        return jsonify({"error": "Stored profile is corrupt"}), 500

    return jsonify(LetterboxdImporter.summarise(profile))


@api_bp.route("/watchlist/export", methods=["POST"])
def export_watchlist():
    """
    Export the given watchlist (the client's localStorage-held liked films,
    sent in the request body) as a Letterboxd-compatible CSV. The user can
    import this back into Letterboxd directly.
    """
    import csv
    import io

    watchlist = request.get_json(silent=True) or []
    if not isinstance(watchlist, list):
        return jsonify({"error": "Expected a JSON array of films"}), 400

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["Title", "Year", "Rating10"])
    writer.writeheader()
    for film in watchlist:
        writer.writerow({
            "Title": film.get("title", ""),
            "Year": str(film.get("release_date", ""))[:4],
            "Rating10": "",
        })

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=cinematch_watchlist.csv"},
    )
