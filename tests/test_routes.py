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
