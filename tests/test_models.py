from app.models import Movie, RatedMovie, TasteProfile
from datetime import date


def test_movie_defaults():
    m = Movie()
    assert m.title == ""
    assert m.vote_average == 0.0
    assert m.similarity_score is None


def test_rated_movie():
    m = RatedMovie(user_rating=4.5, title="Mulholland Drive", watched_date=date(2024, 3, 15))
    assert m.user_rating == 4.5
    assert m.watched_date == date(2024, 3, 15)


def test_taste_profile_top_films():
    profile = TasteProfile(films=[
        RatedMovie(title="Film A", user_rating=3.0),
        RatedMovie(title="Film B", user_rating=5.0),
        RatedMovie(title="Film C", user_rating=4.5),
    ])
    assert profile.top_films[0].title == "Film B"
    assert "film b" in profile.watched_titles
