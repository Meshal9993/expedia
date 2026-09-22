from dataclasses import replace

from fastapi.testclient import TestClient

from backend.controllers.database import DatabaseController
from backend.main import app, get_database
from backend.models.entities import Hotel


def test_hotel_search_contract(tmp_path):
    database = DatabaseController(tmp_path / "expedia.sqlite3")
    database.initialize()
    app.dependency_overrides[get_database] = lambda: database
    try:
        with TestClient(app) as client:
            success = client.get("/api/hotels", params={"name": "harbor lantern"})
            assert success.status_code == 200
            assert [stay["trip_name"] for stay in success.json()["results"]] == [
                "Boston Harbor Weekend",
                "Boston Autumn Weekend",
            ]
            assert success.json()["results"][0]["nightly_rate_usd"] == 150

            database.update(
                replace(
                    database.get(Hotel, "H001"),
                    hotel_name="SQLite Harbor Hotel",
                )
            )
            sqlite_result = client.get(
                "/api/hotels", params={"name": "SQLite Harbor"}
            )
            assert sqlite_result.status_code == 200
            assert len(sqlite_result.json()["results"]) == 2
            assert {
                stay["hotel_name"] for stay in sqlite_result.json()["results"]
            } == {"SQLite Harbor Hotel"}
            assert client.get(
                "/api/hotels", params={"name": "Harbor Lantern"}
            ).json() == {"results": []}

            no_results = client.get("/api/hotels", params={"name": "IST402"})
            assert no_results.status_code == 200
            assert no_results.json() == {"results": []}

            blank = client.get("/api/hotels", params={"name": "  "})
            assert blank.json() == {"results": []}
    finally:
        app.dependency_overrides.clear()
