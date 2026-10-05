"""Check the additive classroom schema without calling a live provider."""

import sqlite3

import pytest

from backend.controllers.database import DatabaseController


@pytest.fixture
def database(tmp_path):
    controller = DatabaseController(tmp_path / "expedia.sqlite3")
    controller.initialize()
    return controller


def insert_hotel(connection, hotel_id="Provider:001", latitude=40.8, longitude=-77.8):
    connection.execute(
        "INSERT INTO saved_hotels (hotel_id, latitude, longitude) VALUES (?, ?, ?)",
        (hotel_id, latitude, longitude),
    )


@pytest.mark.parametrize("existing", [False, True])
def test_migration_preserves_old_and_new_records(tmp_path, existing):
    database = DatabaseController(tmp_path / "expedia.sqlite3")
    if existing:
        database.initialize()
        with database.open() as connection:
            # Reproduce the pre-Part-2 tables and a locally edited record.
            connection.execute("DROP TABLE saved_hotel_locations")
            connection.execute("DROP TABLE demo_hotel_nights")
            connection.execute("DROP TABLE saved_hotels")
            connection.execute("UPDATE users SET display_name = 'Local edit' WHERE user_id = 'U001'")
            before = {
                table: (connection.execute(
                    "SELECT sql FROM sqlite_master WHERE name = ?", (table,)
                ).fetchone()[0], [tuple(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1")])
                for table in ("hotels", "users", "trips", "bookings", "metadata")
            }

    database.initialize()
    with database.open() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        for table, count in (("hotels", 8), ("users", 6), ("trips", 12), ("bookings", 6)):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == count
        assert connection.execute("SELECT COUNT(*) FROM saved_hotels").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM demo_hotel_nights").fetchone()[0] == 0
        if existing:
            for table, (schema, rows) in before.items():
                assert connection.execute(
                    "SELECT sql FROM sqlite_master WHERE name = ?", (table,)
                ).fetchone()[0] == schema
                assert [tuple(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1")] == rows
        insert_hotel(connection)
        connection.execute(
            "INSERT INTO demo_hotel_nights VALUES (?, ?, ?, ?)",
            ("Provider:001", "2026-10-01", 22500, 3),
        )

    database.initialize()
    database.initialize()
    with database.open() as connection:
        assert tuple(connection.execute("SELECT * FROM demo_hotel_nights").fetchone()) == (
            "Provider:001", "2026-10-01", 22500, 3,
        )
        assert connection.execute("SELECT COUNT(*) FROM saved_hotels").fetchone()[0] == 1
    database.check_references()


def test_provider_identity_nullable_fields_and_unique_nights(database):
    provider_id = "001:MixedCase Provider ID "
    with database.open() as connection:
        insert_hotel(connection, provider_id, -90, 180)
        row = connection.execute("SELECT * FROM saved_hotels").fetchone()
        assert row["hotel_id"] == provider_id
        assert row["name"] is None and row["address"] is None
        with pytest.raises(sqlite3.IntegrityError):
            insert_hotel(connection, provider_id)
        insert_hotel(connection, provider_id.lower())
        connection.execute(
            "INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)",
            (provider_id, "2028-02-29"),
        )
        row = connection.execute("SELECT * FROM demo_hotel_nights").fetchone()
        assert row["nightly_rate_cents"] == 10000
        assert row["rooms_available"] == 20
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)",
                (provider_id, "2028-02-29"),
            )
        connection.execute(
            "INSERT INTO demo_hotel_nights VALUES (?, ?, 0, 0)",
            (provider_id, "2028-03-01"),
        )


@pytest.mark.parametrize("latitude, longitude", [
    (91, 0), (-91, 0), (0, 181), (0, -181), (None, 0), (0, None),
    (float("inf"), 0), (0, float("nan")), ("invalid", 0), (0, "invalid"),
])
def test_invalid_coordinates_rejected(database, latitude, longitude):
    with database.open() as connection, pytest.raises(sqlite3.IntegrityError):
        insert_hotel(connection, latitude=latitude, longitude=longitude)


@pytest.mark.parametrize("stay_date", [
    "2026-2-01", "2026-02-30", "2026-02-29", "2026-13-01",
    "2026-10-01T00:00:00", "invalid", None,
])
def test_invalid_dates_rejected(database, stay_date):
    with database.open() as connection:
        insert_hotel(connection)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)",
                ("Provider:001", stay_date),
            )


@pytest.mark.parametrize("column", ["nightly_rate_cents", "rooms_available"])
@pytest.mark.parametrize("value", [-1, 1.5, None])
def test_invalid_demo_values_rejected(database, column, value):
    with database.open() as connection:
        insert_hotel(connection)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                f"INSERT INTO demo_hotel_nights (hotel_id, stay_date, {column}) VALUES (?, ?, ?)",
                ("Provider:001", "2026-10-01", value),
            )


def test_demo_nights_require_saved_hotel_and_restrict_delete(database):
    with database.open() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)",
                ("unknown", "2026-10-01"),
            )
        insert_hotel(connection)
        connection.execute(
            "INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)",
            ("Provider:001", "2026-10-01"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM saved_hotels WHERE hotel_id = ?", ("Provider:001",))
