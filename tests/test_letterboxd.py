import io
import csv
from app.services.letterboxd import LetterboxdImporter


def _make_csv(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["Name", "Year", "Rating", "Watched Date"])
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode()


def test_letterboxd_parse_basic(app):
    with app.app_context():
        raw = _make_csv([
            {"Name": "Stalker", "Year": 1979, "Rating": 4.5, "Watched Date": "2024-01-01"},
            {"Name": "The Shining", "Year": 1980, "Rating": 5.0, "Watched Date": "2024-02-15"},
        ])
        importer = LetterboxdImporter()
        profile = importer.from_csv_bytes(raw)

    assert len(profile.films) == 2
    assert profile.top_films[0].title in ("The Shining", "Stalker")
    assert profile.top_films[0].user_rating == 5.0


def test_letterboxd_summary(app):
    with app.app_context():
        raw = _make_csv([
            {"Name": "Mulholland Drive", "Year": 2001, "Rating": 5.0, "Watched Date": "2024-03-15"},
        ])
        importer = LetterboxdImporter()
        profile = importer.from_csv_bytes(raw)
        summary = LetterboxdImporter.summarise(profile)

    assert summary["total_films"] == 1
    assert isinstance(summary["top_films"], list)
