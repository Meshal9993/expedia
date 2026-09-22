import sqlite3
from dataclasses import replace

import pytest

from backend.controllers.database import DatabaseController
from backend.models.entities import Booking, Hotel, Trip, User


@pytest.fixture
def database(tmp_path):
    controller = DatabaseController(tmp_path / "expedia.sqlite3")
    controller.initialize()
    return controller


def test_csv_seed_and_relationships(database):
    assert len(database.list(Hotel)) == 8
    assert len(database.list(Trip)) == 12
    assert len(database.list(User)) == 6
    assert len(database.list(Booking)) == 6
    assert database.get(Trip, "T001").hotel_id == "H001"
    assert database.get(Booking, "B001").user_id == "U001"
    assert database.get(Booking, "B001").trip_id == "T001"
    with database.open() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }.issuperset({"hotels", "trips", "users", "bookings"})
    database.check_references()


@pytest.mark.parametrize(
    ("model", "entity", "updated"),
    [
        (Hotel, Hotel("H900", "Test Hotel", "Boston", "MA", 99), "Updated Hotel"),
        (Trip, Trip("T900", "H001", "Test Stay", "2026-11-01", "2026-11-02"), "Updated Stay"),
        (User, User("U900", "Test Traveler"), "Updated Traveler"),
        (Booking, Booking("B900", "U001", "T001", "2026-09-10", "confirmed"), "cancelled"),
    ],
)
def test_crud_persists_for_each_model(database, model, entity, updated):
    id_column = next(field for field in entity.__dataclass_fields__ if field.endswith("_id"))
    record_id = getattr(entity, id_column)
    field_to_update = {
        Hotel: "hotel_name",
        Trip: "trip_name",
        User: "display_name",
        Booking: "status",
    }[model]

    assert database.create(entity) == entity
    assert database.get(model, record_id) == entity
    changed = replace(entity, **{field_to_update: updated})
    assert database.update(changed) == changed
    assert database.get(model, record_id) == changed

    reopened = DatabaseController(database.path)
    reopened.initialize()
    assert reopened.get(model, record_id) == changed
    reopened.delete(model, record_id)
    with pytest.raises(KeyError):
        reopened.get(model, record_id)


def test_foreign_keys_and_restricted_deletes(database):
    with pytest.raises(sqlite3.IntegrityError):
        database.create(database.get(Hotel, "H001"))
    with pytest.raises(sqlite3.IntegrityError):
        database.create(Trip("T901", "H999", "Invalid", "2026-11-01", "2026-11-02"))
    with pytest.raises(sqlite3.IntegrityError):
        database.create(Booking("B901", "U999", "T001", "2026-09-10", "confirmed"))
    with pytest.raises(sqlite3.IntegrityError):
        database.update(replace(database.get(Booking, "B001"), trip_id="T999"))
    with pytest.raises(sqlite3.IntegrityError):
        database.delete(Hotel, "H001")
    with pytest.raises(sqlite3.IntegrityError):
        database.delete(User, "U001")
    with pytest.raises(KeyError):
        database.update(User("U999", "Missing"))
    with pytest.raises(KeyError):
        database.delete(User, "U999")
    database.check_references()


def test_booking_lifecycle_persists_without_reseeding(database):
    starter_counts = {
        model: len(database.list(model))
        for model in (Hotel, Trip, User, Booking)
    }
    booking = Booking("B900", "U006", "T012", "2026-09-21", "confirmed")
    database.create(booking)

    reopened = DatabaseController(database.path)
    reopened.initialize()
    assert reopened.get(Booking, "B900") == booking
    assert {
        model: len(reopened.list(model))
        for model in (Hotel, Trip, User, Booking)
    } == {**starter_counts, Booking: starter_counts[Booking] + 1}

    cancelled = replace(booking, status="cancelled")
    reopened.update(cancelled)
    reopened = DatabaseController(database.path)
    reopened.initialize()
    assert reopened.get(Booking, "B900") == cancelled

    reopened.delete(Booking, "B900")
    reopened = DatabaseController(database.path)
    reopened.initialize()
    with pytest.raises(KeyError):
        reopened.get(Booking, "B900")
    assert {
        model: len(reopened.list(model))
        for model in (Hotel, Trip, User, Booking)
    } == starter_counts
