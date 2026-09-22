from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.controllers.booking import (
    BookingController,
    BookingNotFoundError,
    BookingReferenceError,
)
from backend.controllers.database import DatabaseController
from backend.main import app, get_database
from backend.models.entities import Booking


@pytest.fixture
def database(tmp_path):
    controller = DatabaseController(tmp_path / "expedia.sqlite3")
    controller.initialize()
    return controller


@pytest.fixture
def booking_controller(database):
    return BookingController(database)


def test_successful_booking_creation_and_details(booking_controller, database):
    details = booking_controller.create_booking(
        "U006", "T012", date(2026, 9, 21)
    )

    assert details["booking"] == {
        "booking_id": "B007",
        "user_id": "U006",
        "trip_id": "T012",
        "booked_on": "2026-09-21",
        "status": "confirmed",
    }
    assert details["traveler"]["display_name"] == "Demo Traveler 6"
    assert details["trip"]["trip_name"] == "Washington Autumn Break"
    assert details["hotel"]["hotel_name"] == "Capitol Grove Hotel"
    assert database.get(Booking, "B007").status == "confirmed"


@pytest.mark.parametrize(
    ("user_id", "trip_id", "message"),
    [
        ("U999", "T001", "Traveler 'U999' was not found"),
        ("U001", "T999", "Trip 'T999' was not found"),
    ],
)
def test_booking_creation_rejects_invalid_references(
    booking_controller, user_id, trip_id, message
):
    with pytest.raises(BookingReferenceError, match=message):
        booking_controller.create_booking(
            user_id, trip_id, date(2026, 9, 21)
        )


def test_booking_history_and_user_filter(booking_controller):
    created = booking_controller.create_booking(
        "U001", "T012", date(2026, 9, 21)
    )

    history = booking_controller.get_history()
    assert len(history) == 7
    assert created in history

    user_history = booking_controller.get_history("U001")
    assert len(user_history) == 3
    assert all(item["traveler"]["user_id"] == "U001" for item in user_history)
    assert {item["booking"]["booking_id"] for item in user_history} == {
        "B001",
        "B002",
        "B007",
    }


def test_retrieve_cancel_and_delete_booking(booking_controller, database):
    created = booking_controller.create_booking(
        "U006", "T012", date(2026, 9, 21)
    )
    booking_id = created["booking"]["booking_id"]

    assert booking_controller.get_booking(booking_id) == created
    cancelled = booking_controller.cancel_booking(booking_id)
    assert cancelled["booking"]["status"] == "cancelled"
    assert len(database.list(Booking)) == 7
    assert database.get(Booking, booking_id).status == "cancelled"

    assert booking_controller.delete_booking(booking_id) == {
        "booking_id": booking_id,
        "deleted": True,
    }
    with pytest.raises(BookingNotFoundError):
        booking_controller.get_booking(booking_id)
    with pytest.raises(BookingNotFoundError):
        booking_controller.cancel_booking(booking_id)
    with pytest.raises(BookingNotFoundError):
        booking_controller.delete_booking(booking_id)


def test_booking_changes_persist_after_database_reopens(booking_controller, database):
    created = booking_controller.create_booking(
        "U006", "T012", date(2026, 9, 21)
    )
    booking_id = created["booking"]["booking_id"]

    reopened_database = DatabaseController(database.path)
    reopened_database.initialize()
    reopened_controller = BookingController(reopened_database)
    assert reopened_controller.get_booking(booking_id) == created

    reopened_controller.cancel_booking(booking_id)
    reopened_database = DatabaseController(database.path)
    reopened_database.initialize()
    assert BookingController(reopened_database).get_booking(booking_id)[
        "booking"
    ]["status"] == "cancelled"
    assert len(reopened_database.list(Booking)) == 7


def test_booking_http_lifecycle(database):
    app.dependency_overrides[get_database] = lambda: database
    try:
        with TestClient(app) as client:
            create_response = client.post(
                "/api/bookings",
                json={
                    "user_id": "U006",
                    "trip_id": "T012",
                    "booked_on": "2026-09-21",
                },
            )
            assert create_response.status_code == 201
            created = create_response.json()
            booking_id = created["booking"]["booking_id"]
            assert created["booking"]["status"] == "confirmed"

            read_response = client.get(f"/api/bookings/{booking_id}")
            assert read_response.status_code == 200
            assert read_response.json() == created

            history_response = client.get("/api/bookings")
            assert history_response.status_code == 200
            assert created in history_response.json()["bookings"]

            user_history = client.get(
                "/api/bookings", params={"user_id": "U006"}
            )
            assert user_history.status_code == 200
            assert user_history.json() == {"bookings": [created]}

            cancel_response = client.patch(
                f"/api/bookings/{booking_id}",
                json={"status": "cancelled"},
            )
            assert cancel_response.status_code == 200
            cancelled = cancel_response.json()
            assert cancelled["booking"]["status"] == "cancelled"
            assert client.get(f"/api/bookings/{booking_id}").json() == cancelled

            delete_response = client.delete(f"/api/bookings/{booking_id}")
            assert delete_response.status_code == 200
            assert delete_response.json() == {
                "booking_id": booking_id,
                "deleted": True,
            }
            assert client.get(f"/api/bookings/{booking_id}").status_code == 404
            assert client.delete(f"/api/bookings/{booking_id}").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_booking_http_errors(database):
    app.dependency_overrides[get_database] = lambda: database
    try:
        with TestClient(app) as client:
            invalid_user = client.post(
                "/api/bookings",
                json={
                    "user_id": "U999",
                    "trip_id": "T001",
                    "booked_on": "2026-09-21",
                },
            )
            assert invalid_user.status_code == 404
            assert invalid_user.json() == {
                "detail": "Traveler 'U999' was not found"
            }

            invalid_trip = client.post(
                "/api/bookings",
                json={
                    "user_id": "U001",
                    "trip_id": "T999",
                    "booked_on": "2026-09-21",
                },
            )
            assert invalid_trip.status_code == 404
            assert invalid_trip.json() == {"detail": "Trip 'T999' was not found"}

            assert client.get(
                "/api/bookings", params={"user_id": "U999"}
            ).status_code == 404
            assert client.get("/api/bookings/B999").status_code == 404
            assert client.patch(
                "/api/bookings/B001", json={"status": "confirmed"}
            ).status_code == 422
    finally:
        app.dependency_overrides.clear()
