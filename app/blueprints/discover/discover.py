from flask import Blueprint, render_template, session

discover_bp = Blueprint(
    "discover_bp", __name__, template_folder="templates", static_folder="static"
)


@discover_bp.route("/discover")
def discover():
    recommendations = session.get("recommendations", [])
    return render_template("discover.html", recommendations=recommendations)
