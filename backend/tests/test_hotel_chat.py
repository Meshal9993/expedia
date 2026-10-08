"""RAG checks use fixed fixture data, temporary SQLite, and mocked OpenAI only."""

import asyncio
import json
from datetime import date
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.controllers.chat import ChatController
from backend.controllers.database import DatabaseController
from backend.controllers.hotel_chat import HotelChatController, assess_stay
from backend.controllers.hotel_sql import HotelRetrievalError, RejectedHotelSql
from backend.main import app, get_hotel_chat_controller
from backend.models.hotel_chat import HotelChatRequest, SqlProposal
from backend.models.saved_hotels import SavedHotel, SavedSearchCenter


FIXTURE = Path(__file__).resolve().parents[2] / "docs/assignment2-part2-rag-fixture.json"
JOIN_SQL = (
    "SELECT h.hotel_id, h.name, l.requested_zip, n.stay_date, n.nightly_rate_cents, n.rooms_available "
    "FROM saved_hotels h JOIN saved_hotel_locations l ON h.hotel_id = l.hotel_id "
    "LEFT JOIN demo_hotel_nights n ON h.hotel_id = n.hotel_id "
    "AND n.stay_date >= ? AND n.stay_date < ? WHERE l.requested_zip = ? "
    "AND h.hotel_id = ? ORDER BY n.stay_date"
)
STAY = {"check_in": "2026-10-10", "check_out": "2026-10-13", "rooms": 2}
KEY = "mock-rag-credential"


@pytest.fixture
def database(tmp_path):
    database = DatabaseController(tmp_path / "hotels.sqlite3")
    database.initialize()
    for item in json.loads(FIXTURE.read_text())["hotels"]:
        database.save_api_hotel(
            SavedHotel(place_id=item["hotel_id"], **{key: item[key] for key in ("name", "latitude", "longitude")},
                       formatted_address=item["address"]),
            SavedSearchCenter(**item["location"]),
            tuple(date.fromisoformat(night["stay_date"]) for night in item["nights"]),
        )
        with database.open() as connection:
            for night in item["nights"]:
                connection.execute("UPDATE demo_hotel_nights SET nightly_rate_cents = ?, rooms_available = ? "
                                   "WHERE hotel_id = ? AND stay_date = ?",
                                   (night["nightly_rate_cents"], night["rooms_available"],
                                    item["hotel_id"], night["stay_date"]))
    return database


def proposal(hotel_id="fixture-alpha", zip_code="02108"):
    return SqlProposal(sql=JOIN_SQL, parameters=[STAY["check_in"], STAY["check_out"], zip_code, hotel_id], stay=STAY)


def model_response(value):
    return httpx.Response(200, json={"status": "completed", "output": [{
        "type": "message", "content": [{"type": "output_text", "text": json.dumps(value)}],
    }]})


def test_approved_join_leading_zero_and_checkout_exclusion(database):
    result = database.retrieve_hotel_records(proposal())
    assert len(result.records) == 3
    assert {row["requested_zip"] for row in result.records} == {"02108"}
    assert all(type(row["requested_zip"]) is str for row in result.records)
    assert {row["stay_date"] for row in result.records} == {"2026-10-10", "2026-10-11", "2026-10-12"}
    assessment = assess_stay(proposal(), result.records)[0]
    assert assessment.total_rate_cents == 31000
    assert assessment.enough_rooms is True
    assert assessment.missing_dates == []
    assert "LIMIT 51" in result.executed_sql


@pytest.mark.parametrize("sql", [
    "INSERT INTO saved_hotels (hotel_id) VALUES (?)",
    "UPDATE saved_hotels SET name = ?",
    "DELETE FROM saved_hotels", "DROP TABLE saved_hotels", "ALTER TABLE saved_hotels ADD COLUMN x TEXT",
    "CREATE TABLE x (id TEXT)", "REPLACE INTO saved_hotels (hotel_id) VALUES (?)",
    "PRAGMA table_info(saved_hotels)", "ATTACH DATABASE ? AS extra", "DETACH extra", "VACUUM",
    "BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT x",
    "SELECT hotel_id FROM saved_hotels; DELETE FROM saved_hotels",
    "SELECT hotel_id FROM saved_hotels -- hidden", "SELECT hotel_id FROM saved_hotels /* hidden */",
    "SELECT name FROM sqlite_master", "SELECT user_id FROM users",
    "SELECT event_id FROM chat_events", "SELECT conversation_id FROM chat_conversations",
    "SELECT not_a_column FROM saved_hotels",
    "SELECT name FROM saved_hotels WHERE load_extension(?) IS NULL",
    "SELECT name FROM saved_hotels WHERE length(randomblob(?)) > ?",
    "SELECT ? AS nightly_rate_cents FROM saved_hotels",
    "SELECT name AS nightly_rate_cents FROM saved_hotels",
    "SELECT hotel_id FROM saved_hotels UNION SELECT hotel_id FROM hotels",
    "WITH x AS (SELECT hotel_id FROM saved_hotels) SELECT hotel_id FROM x",
    "SELECT hotel_id FROM saved_hotels WHERE name = 'inline user text'",
    "SELECT hotel_id FROM saved_hotels LIMIT 1000",
    "SELECT h.hotel_id, n.rooms_available FROM saved_hotels h CROSS JOIN demo_hotel_nights n",
    "SELECT h.hotel_id, n.rooms_available FROM saved_hotels h JOIN demo_hotel_nights n ON h.hotel_id = n.hotel_id OR ? = ?",
])
def test_unsafe_queries_rejected_and_all_tables_unchanged(database, sql):
    with database.open() as connection:
        before = {table: connection.execute(f"SELECT * FROM {table}").fetchall()
                  for table in ("saved_hotels", "demo_hotel_nights", "hotels", "users", "trips", "bookings")}
    with pytest.raises(RejectedHotelSql):
        database.retrieve_hotel_records(SqlProposal(sql=sql, parameters=[1] * sql.count("?")))
    with database.open() as connection:
        assert before == {table: connection.execute(f"SELECT * FROM {table}").fetchall() for table in before}


def test_parameter_count_and_zip_type_are_checked(database):
    for values in ([], [2108]):
        with pytest.raises(RejectedHotelSql):
            database.retrieve_hotel_records(SqlProposal(sql="SELECT hotel_id FROM saved_hotel_locations WHERE requested_zip = ?", parameters=values))


def test_bounded_rows_and_output(database):
    for index in range(60):
        database.save_api_hotel(SavedHotel(place_id=f"bounded-{index}", latitude=42.0, longitude=-71.0),
                                SavedSearchCenter(requested_zip="02108", resolved_postcode="02108", latitude=42.0, longitude=-71.0), ())
    result = database.retrieve_hotel_records(SqlProposal(
        sql="SELECT hotel_id FROM saved_hotels ORDER BY hotel_id",
        parameters=[],
    ))
    assert len(result.records) == 50 and result.truncated
    with database.open() as connection:
        connection.execute("UPDATE saved_hotels SET address = ?", ("x" * 15000,))
    result = database.retrieve_hotel_records(SqlProposal(sql="SELECT hotel_id, address FROM saved_hotels", parameters=[]))
    assert result.truncated and len(json.dumps(result.records).encode()) <= 32768


def test_execution_deadline(database, monkeypatch):
    times = iter([0, 0, 2])
    monkeypatch.setattr("backend.controllers.database.monotonic", lambda: next(times, 2))
    monkeypatch.setattr("backend.controllers.database.QUERY_PROGRESS_INTERVAL", 1)
    with pytest.raises(HotelRetrievalError):
        database.retrieve_hotel_records(proposal())


def test_missing_night_never_has_full_total_or_availability(database):
    query = proposal("fixture-missing-night")
    assessment = assess_stay(query, database.retrieve_hotel_records(query).records)[0]
    assert assessment.missing_dates == ["2026-10-11"]
    assert assessment.total_rate_cents is None and assessment.enough_rooms is None


def test_readonly_uri_is_used_and_numeric_parameters_are_bounded(database, monkeypatch):
    import sqlite3
    from pydantic import ValidationError
    original = sqlite3.connect
    connections = []
    def observe(path, **options):
        connections.append((path, options))
        return original(path, **options)
    monkeypatch.setattr("backend.controllers.database.sqlite3.connect", observe)
    database.retrieve_hotel_records(proposal())
    assert len(connections) == 1
    assert connections[0][0].endswith("?mode=ro") and connections[0][1]["uri"] is True
    for value in (True, 2**80, float("inf")):
        with pytest.raises(ValidationError):
            SqlProposal(sql="SELECT hotel_id FROM saved_hotels WHERE hotel_id = ?", parameters=[value])


@pytest.fixture
def route(database):
    calls = []
    def invoke(query=None, second=None, first_failure=None, payload=None):
        def provider(request):
            calls.append(json.loads(request.content))
            if len(calls) % 2 == 1:
                return first_failure or model_response((query or proposal()).model_dump(mode="json"))
            return second or model_response({"answer": "Fixture Alpha Hotel has three simulated nights totaling $310.00.",
                                             "hotel_ids": ["fixture-alpha"]})
        client = httpx.AsyncClient(transport=httpx.MockTransport(provider))
        controller = HotelChatController(database, ChatController(client=client, api_key=KEY))
        app.dependency_overrides[get_hotel_chat_controller] = lambda: controller
        try:
            with TestClient(app) as frontend:
                response = frontend.post("/api/hotel-chat", json=payload or {
                    "question": "Find fixture-alpha in ZIP 02108 for 2026-10-10 to 2026-10-13, two rooms.",
                })
        finally:
            app.dependency_overrides.clear()
            asyncio.run(client.aclose())
        return response
    yield invoke, calls
    app.dependency_overrides.clear()


def test_two_mocked_requests_grounding_trace_and_reopening(database, route):
    invoke, calls = route
    response = invoke()
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "answer" and body["simulated_data"]
    assert body["stay_assessments"][0]["total_rate_cents"] == 31000
    assert body["parameters"][2] == "02108"
    assert len(calls) == 2 and calls[0]["text"]["format"]["type"] == "json_schema"
    assert calls[0]["store"] is False and calls[1]["store"] is False
    evidence = json.loads(calls[1]["input"][0]["content"])
    assert evidence["question"] == body["question"]
    assert evidence["retrieved_records"] == body["retrieved_records"]
    assert "simulated classroom data" in body["answer"]
    assert KEY not in json.dumps(body) + json.dumps(calls)
    reopened = DatabaseController(database.path)
    from uuid import UUID
    history = reopened.get_chat_history(UUID(body["conversation_id"]))
    assert [event.stage for event in history.events] == ["user", "proposed_sql", "executed_sql", "retrieval_result", "assistant"]
    assert history.events[-1].content["answer"] == body["answer"]
    assert history.conversation.prompt_hash and history.conversation.prompt_version == "hotel-assistant-v1"
    controller = HotelChatController(reopened, ChatController(api_key=""))
    app.dependency_overrides[get_hotel_chat_controller] = lambda: controller
    try:
        with TestClient(app) as client:
            saved = client.get(f"/api/hotel-chat/{body['conversation_id']}")
            assert saved.status_code == 200 and saved.json()["events"][-1]["content"] == body
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("hotel,zip_code,state", [("fixture-alpha", "99999", "no_matches"),
                                                ("fixture-missing-night", "02108", "insufficient_data")])
def test_empty_and_insufficient_states_are_not_provider_failures(route, hotel, zip_code, state):
    invoke, calls = route
    response = invoke(query=proposal(hotel, zip_code), second=model_response({"answer": "Untrusted positive claim", "hotel_ids": []}),
                      payload={"question": f"Find saved hotels in ZIP {zip_code} for 2026-10-10 to 2026-10-13."})
    assert response.status_code == 200 and response.json()["state"] == state
    assert "Untrusted positive" not in response.json()["answer"]
    assert len(calls) == 2


def test_oversized_first_record_is_insufficient_not_no_matches(database, route):
    with database.open() as connection:
        connection.execute("UPDATE saved_hotels SET address = ? WHERE hotel_id = ?",
                           ("x" * 40000, "fixture-alpha"))
    invoke, calls = route
    response = invoke(
        query=SqlProposal(sql="SELECT hotel_id, address FROM saved_hotels WHERE hotel_id = ?",
                          parameters=["fixture-alpha"]),
        second=model_response({"answer": "Untrusted positive claim", "hotel_ids": []}),
        payload={"question": "Show the saved address for fixture-alpha."},
    )
    body = response.json()
    assert response.status_code == 200 and body["state"] == "insufficient_data"
    assert body["truncated"] and body["retrieved_records"] == []
    assert "insufficient evidence" in body["answer"] and "Untrusted positive" not in body["answer"]
    assert len(calls) == 2


@pytest.mark.parametrize("status,code", [(500, "unavailable"), (429, "limited"), (401, "configuration")])
def test_model_failure_distinct_and_safe(database, route, status, code):
    invoke, calls = route
    response = invoke(first_failure=httpx.Response(status, json={"error": {"message": KEY}}))
    assert response.status_code != 200 and response.json()["code"] == code
    assert KEY not in response.text and len(calls) == 1
    from uuid import UUID
    history = database.get_chat_history(UUID(response.json()["conversation_id"]))
    assert [event.stage for event in history.events] == ["user", "model_error"]


def test_rejected_model_sql_is_not_empty_success(route):
    invoke, calls = route
    response = invoke(query=SqlProposal(sql="DELETE FROM saved_hotels", parameters=[], stay=STAY))
    assert response.status_code == 422 and response.json()["code"] == "rejected_sql"
    assert len(calls) == 1


def test_answer_cannot_cite_unretrieved_hotel(route):
    invoke, _ = route
    response = invoke(second=model_response({"answer": "Invented alternative", "hotel_ids": ["not-retrieved"]}))
    assert response.status_code == 502 and response.json()["code"] == "model_invalid"


def test_model_arithmetic_cannot_override_complete_nightly_evidence(route):
    invoke, _ = route
    response = invoke(second=model_response({"answer": "Price is $1.00 and checkout is included.", "hotel_ids": ["fixture-alpha"]}))
    assert response.status_code == 200
    assert "$310.00" in response.json()["answer"] and "$1.00" not in response.json()["answer"]


def test_changed_zip_or_stay_is_rejected_before_retrieval(route):
    invoke, calls = route
    response = invoke(query=proposal(zip_code="16801"))
    assert response.status_code == 422 and response.json()["code"] == "rejected_sql"
    assert len(calls) == 1


def test_second_model_failure_keeps_retrieval_trace(database, route):
    invoke, _ = route
    response = invoke(second=httpx.Response(500, json={"error": {"message": KEY}}))
    assert response.json()["code"] == "unavailable" and KEY not in response.text
    from uuid import UUID
    history = database.get_chat_history(UUID(response.json()["conversation_id"]))
    assert [event.stage for event in history.events] == ["user", "proposed_sql", "executed_sql", "retrieval_result", "model_error"]


def test_readonly_database_failure_is_distinct(database, route, monkeypatch):
    invoke, _ = route
    monkeypatch.setattr(database, "retrieve_hotel_records", lambda _: (_ for _ in ()).throw(HotelRetrievalError()))
    response = invoke()
    assert response.status_code == 503 and response.json()["code"] == "retrieval_failed"


def test_unknown_conversation_and_invalid_input(database):
    from uuid import uuid4
    controller = HotelChatController(database, ChatController(api_key=""))
    app.dependency_overrides[get_hotel_chat_controller] = lambda: controller
    try:
        with TestClient(app) as client:
            assert client.get(f"/api/hotel-chat/{uuid4()}").status_code == 404
            assert client.post("/api/hotel-chat", json={"question": "   "}).status_code == 422
            assert client.post("/api/hotel-chat", json={"question": "Hi", "sql": "SELECT hotel_id FROM saved_hotels"}).status_code == 422
    finally:
        app.dependency_overrides.clear()
