import csv
import io
from unittest.mock import Mock, patch

import pytest

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


_SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:letterboxd="https://letterboxd.com" xmlns:tmdb="https://themoviedb.org">
<channel>
<title>testuser's diary</title>
<item>
  <title>Stalker, 1979 - &#9733;&#9733;&#9733;&#9733;&#9733;</title>
  <link>https://letterboxd.com/testuser/film/stalker/</link>
  <guid isPermaLink="false">letterboxd-watch-1</guid>
  <letterboxd:watchedDate>2024-01-01</letterboxd:watchedDate>
  <letterboxd:filmTitle>Stalker</letterboxd:filmTitle>
  <letterboxd:filmYear>1979</letterboxd:filmYear>
  <letterboxd:memberRating>5</letterboxd:memberRating>
  <tmdb:movieId>1234</tmdb:movieId>
</item>
<item>
  <title>Some Unrated Film, 2020</title>
  <link>https://letterboxd.com/testuser/film/some-unrated-film/</link>
  <guid isPermaLink="false">letterboxd-watch-2</guid>
  <letterboxd:watchedDate>2024-01-02</letterboxd:watchedDate>
  <letterboxd:filmTitle>Some Unrated Film</letterboxd:filmTitle>
  <letterboxd:filmYear>2020</letterboxd:filmYear>
</item>
</channel>
</rss>
"""


def test_rss_import_parses_feed_and_skips_unrated(app):
    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()
    mock_resp.raw.read = Mock(return_value=_SAMPLE_RSS)

    with app.app_context(), patch("app.services.letterboxd.requests.get", return_value=mock_resp):
        importer = LetterboxdImporter()
        profile = importer.from_rss_username("testuser")

    assert len(profile.films) == 1  # the unrated entry is skipped
    assert profile.films[0].title == "Stalker"
    assert profile.films[0].user_rating == 5.0


@pytest.mark.parametrize("bad_username", ["../etc/passwd", "user name", "user@host", ""])
def test_rss_import_rejects_invalid_username(app, bad_username):
    with app.app_context():
        importer = LetterboxdImporter()
        with pytest.raises(ValueError):
            importer.from_rss_username(bad_username)
