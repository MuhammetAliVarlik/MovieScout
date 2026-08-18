def test_home_returns_200(client):
    res = client.get("/")
    assert res.status_code == 200


def test_search_movies_empty_query(client):
    res = client.post("/search_movies", data={"movieName": ""})
    assert res.status_code == 200
    assert res.json == []


def test_import_no_file_returns_400(client):
    res = client.post("/api/import")
    assert res.status_code == 400


def test_discover_returns_200(client):
    res = client.get("/discover")
    assert res.status_code == 200


def test_watchlist_export_empty_list(client):
    res = client.post("/api/watchlist/export", json=[])
    assert res.status_code == 200
    assert res.mimetype == "text/csv"


def test_find_similar_movies_multi_seed(client):
    # 5 movies mirrors the real auto-seed count from a Letterboxd import —
    # regression check for the multi-movie embedding text exceeding the
    # model's token limit and silently truncating later picks.
    res = client.post(
        "/find_similar_movies",
        data={
            "movies[]": [
                "Test Movie One",
                "Test Movie Two",
                "Test Movie Three",
                "Test Movie Four",
                "Test Movie Five",
            ]
        },
    )
    assert res.status_code == 200
    assert res.json["status"] == "success"


def test_find_similar_movies_handles_missing_fields(client):
    # "Test Movie Seven" has blank overview/genres/poster_path/backdrop_path/
    # release_date — regression check for NaN (from pandas) reaching Movie's
    # pydantic validation, which crashed whenever a candidate result had no
    # poster/backdrop image (common at real TMDB scale, rare in small fixtures).
    res = client.post("/find_similar_movies", data={"movies[]": ["Test Movie Seven"]})
    assert res.status_code == 200
    assert res.json["status"] == "success"
