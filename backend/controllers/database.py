"""SQLite persistence for instructor entities and separate classroom hotel data."""

import csv
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Iterator, List

from backend.models.entities import Booking, Hotel, HotelStay, Trip, User
from backend.models.saved_hotels import (
    DemoHotelNight, SavedHotel, SavedHotelSearchResponse, SavedHotelWithNights,
    SavedSearchCenter,
)


Entity = Hotel | Trip | User | Booking
EntityType = type[Hotel] | type[Trip] | type[User] | type[Booking]
DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data"

# Whitelisted table and column names; only values are supplied to SQL at runtime.
TABLES: dict[EntityType, tuple[str, str, tuple[str, ...]]] = {
    Hotel: ("hotels", "hotel_id", ("hotel_id", "hotel_name", "city", "state", "nightly_rate_usd")),
    Trip: ("trips", "trip_id", ("trip_id", "hotel_id", "trip_name", "check_in", "check_out")),
    User: ("users", "user_id", ("user_id", "display_name")),
    Booking: ("bookings", "booking_id", ("booking_id", "user_id", "trip_id", "booked_on", "status")),
}


class DatabaseController:
    """Open the database, enforce references, and offer entity CRUD operations.

    Create/update accept a model instance. Get/list/delete accept a model class.
    Missing get/update/delete IDs raise KeyError. Duplicate IDs and invalid
    foreign-key references raise sqlite3.IntegrityError.
    """

    def __init__(self, path: Path):
        self.path = Path(path)

    @contextmanager
    def open(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        """Apply additive schema updates and seed the read-only CSVs only once."""
        with self.open() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS hotels (
                    hotel_id TEXT PRIMARY KEY,
                    hotel_name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    state TEXT NOT NULL,
                    nightly_rate_usd REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS trips (
                    trip_id TEXT PRIMARY KEY,
                    hotel_id TEXT NOT NULL REFERENCES hotels(hotel_id) ON DELETE RESTRICT,
                    trip_name TEXT NOT NULL,
                    check_in TEXT NOT NULL,
                    check_out TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
                    trip_id TEXT NOT NULL REFERENCES trips(trip_id) ON DELETE RESTRICT,
                    booked_on TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                -- Additive, repeatable Assignment 2 Part 2 schema migration.
                CREATE TABLE IF NOT EXISTS saved_hotels (
                    hotel_id TEXT NOT NULL PRIMARY KEY COLLATE BINARY,
                    name TEXT,
                    address TEXT,
                    latitude REAL NOT NULL CHECK (
                        typeof(latitude) IN ('integer', 'real')
                        AND latitude BETWEEN -90 AND 90
                    ),
                    longitude REAL NOT NULL CHECK (
                        typeof(longitude) IN ('integer', 'real')
                        AND longitude BETWEEN -180 AND 180
                    )
                );
                -- These rates and room counts are fictional classroom defaults.
                CREATE TABLE IF NOT EXISTS demo_hotel_nights (
                    hotel_id TEXT NOT NULL
                        REFERENCES saved_hotels(hotel_id) ON DELETE RESTRICT,
                    stay_date TEXT NOT NULL CHECK (
                        stay_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                        AND date(stay_date, '+0 days') IS NOT NULL
                        AND date(stay_date, '+0 days') = stay_date
                    ),
                    nightly_rate_cents INTEGER NOT NULL DEFAULT 10000 CHECK (
                        typeof(nightly_rate_cents) = 'integer'
                        AND nightly_rate_cents >= 0
                    ),
                    rooms_available INTEGER NOT NULL DEFAULT 20 CHECK (
                        typeof(rooms_available) = 'integer'
                        AND rooms_available >= 0
                    ),
                    PRIMARY KEY (hotel_id, stay_date)
                );
                CREATE TABLE IF NOT EXISTS saved_hotel_locations (
                    hotel_id TEXT NOT NULL
                        REFERENCES saved_hotels(hotel_id) ON DELETE RESTRICT,
                    requested_zip TEXT NOT NULL CHECK (
                        requested_zip GLOB '[0-9][0-9][0-9][0-9][0-9]'
                    ),
                    resolved_postcode TEXT NOT NULL CHECK (resolved_postcode = requested_zip),
                    city TEXT,
                    state TEXT,
                    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
                    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
                    PRIMARY KEY (hotel_id, requested_zip)
                );
                """
            )
            seeded = connection.execute(
                "SELECT 1 FROM metadata WHERE key = 'csv_seeded'"
            ).fetchone()
            if seeded is None:
                if any(connection.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
                       for table, _, _ in TABLES.values()):
                    raise ValueError("Database contains records but has no CSV seed marker")
                self._seed_from_csv(connection)
                connection.execute(
                    "INSERT INTO metadata (key, value) VALUES ('csv_seeded', '1')"
                )
            self._check_references(connection)

    @staticmethod
    def _read_csv(model: EntityType) -> list[Entity]:
        filename = f"{TABLES[model][0]}.csv"
        with (DATA_DIRECTORY / filename).open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if tuple(reader.fieldnames or ()) != TABLES[model][2]:
                raise ValueError(f"Unexpected columns in {filename}")
            records = list(reader)
            if model is Hotel:
                for row in records:
                    row["nightly_rate_usd"] = float(row["nightly_rate_usd"])
            return [model(**row) for row in records]

    def _seed_from_csv(self, connection: sqlite3.Connection) -> None:
        hotels = self._read_csv(Hotel)
        users = self._read_csv(User)
        trips = self._read_csv(Trip)
        bookings = self._read_csv(Booking)

        hotel_ids = {hotel.hotel_id for hotel in hotels}
        user_ids = {user.user_id for user in users}
        trip_ids = {trip.trip_id for trip in trips}
        if any(trip.hotel_id not in hotel_ids for trip in trips):
            raise ValueError("trips.csv contains an unknown hotel_id")
        if any(booking.user_id not in user_ids or booking.trip_id not in trip_ids
               for booking in bookings):
            raise ValueError("bookings.csv contains an unknown user_id or trip_id")

        for entity in (*hotels, *users, *trips, *bookings):
            self._insert(connection, entity)

    @staticmethod
    def _check_references(connection: sqlite3.Connection) -> None:
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise ValueError(f"Database has invalid references: {violations}")

    def check_references(self) -> None:
        """Raise ValueError if stored foreign-key relationships are invalid."""
        with self.open() as connection:
            self._check_references(connection)

    @staticmethod
    def _insert(connection: sqlite3.Connection, entity: Entity) -> None:
        table, _, columns = TABLES[type(entity)]
        values = asdict(entity)
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(values[column] for column in columns),
        )

    def create(self, entity: Entity) -> Entity:
        with self.open() as connection:
            self._insert(connection, entity)
        return entity

    def get(self, model: EntityType, record_id: str) -> Entity:
        table, id_column, _ = TABLES[model]
        with self.open() as connection:
            row = connection.execute(
                f"SELECT * FROM {table} WHERE {id_column} = ?", (record_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"{table} record {record_id!r} not found")
        return model(**dict(row))

    def list(self, model: EntityType) -> list[Entity]:
        table, id_column, _ = TABLES[model]
        with self.open() as connection:
            rows = connection.execute(f"SELECT * FROM {table} ORDER BY {id_column}").fetchall()
        return [model(**dict(row)) for row in rows]

    def update(self, entity: Entity) -> Entity:
        table, id_column, columns = TABLES[type(entity)]
        values = asdict(entity)
        editable = [column for column in columns if column != id_column]
        assignments = ", ".join(f"{column} = ?" for column in editable)
        with self.open() as connection:
            cursor = connection.execute(
                f"UPDATE {table} SET {assignments} WHERE {id_column} = ?",
                tuple(values[column] for column in editable) + (values[id_column],),
            )
            if cursor.rowcount == 0:
                raise KeyError(f"{table} record {values[id_column]!r} not found")
        return entity

    def delete(self, model: EntityType, record_id: str) -> None:
        table, id_column, _ = TABLES[model]
        with self.open() as connection:
            cursor = connection.execute(
                f"DELETE FROM {table} WHERE {id_column} = ?", (record_id,)
            )
            if cursor.rowcount == 0:
                raise KeyError(f"{table} record {record_id!r} not found")

    def search_hotel_stays(self, name: str) -> List[HotelStay]:
        """Return matching hotel/trip records using a read-only SQL join."""
        with self.open() as connection:
            rows = connection.execute(
                """
                SELECT h.hotel_id, h.hotel_name, h.city, h.state, h.nightly_rate_usd,
                       t.trip_id, t.trip_name, t.check_in, t.check_out
                FROM hotels AS h
                JOIN trips AS t ON t.hotel_id = h.hotel_id
                WHERE instr(lower(h.hotel_name), lower(?)) > 0
                ORDER BY t.trip_id
                """,
                (name,),
            ).fetchall()
        return [HotelStay(**dict(row)) for row in rows]

    @staticmethod
    def _saved_hotel(connection: sqlite3.Connection, row: sqlite3.Row) -> SavedHotelWithNights:
        nights = connection.execute(
            "SELECT stay_date, nightly_rate_cents, rooms_available "
            "FROM demo_hotel_nights WHERE hotel_id = ? ORDER BY stay_date",
            (row["hotel_id"],),
        ).fetchall()
        return SavedHotelWithNights(
            place_id=row["hotel_id"], name=row["name"],
            formatted_address=row["address"], latitude=row["latitude"],
            longitude=row["longitude"],
            demo_nights=[DemoHotelNight(**dict(night)) for night in nights],
        )

    def save_api_hotel(
        self, hotel: SavedHotel, center: SavedSearchCenter, stay_dates: tuple[date, ...],
    ) -> SavedHotelWithNights:
        """Atomically save identity, ZIP context, and missing demo nights only."""
        with self.open() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO saved_hotels (hotel_id, name, address, latitude, longitude) "
                "VALUES (?, ?, ?, ?, ?) ON CONFLICT(hotel_id) DO NOTHING",
                (hotel.place_id, hotel.name, hotel.formatted_address, hotel.latitude, hotel.longitude),
            )
            connection.execute(
                "INSERT INTO saved_hotel_locations "
                "(hotel_id, requested_zip, resolved_postcode, city, state, latitude, longitude) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(hotel_id, requested_zip) DO NOTHING",
                (hotel.place_id, center.requested_zip, center.resolved_postcode,
                 center.city, center.state, center.latitude, center.longitude),
            )
            connection.executemany(
                "INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?) "
                "ON CONFLICT(hotel_id, stay_date) DO NOTHING",
                [(hotel.place_id, stay_date.isoformat()) for stay_date in stay_dates],
            )
            row = connection.execute(
                "SELECT * FROM saved_hotels WHERE hotel_id = ?", (hotel.place_id,),
            ).fetchone()
            return self._saved_hotel(connection, row)

    def get_saved_hotels(self, zip_code: str) -> SavedHotelSearchResponse:
        """Return only hotels associated with this exact ZIP and stored context."""
        with self.open() as connection:
            connection.execute("BEGIN")
            context = connection.execute(
                "SELECT requested_zip, resolved_postcode, city, state, latitude, longitude "
                "FROM saved_hotel_locations WHERE requested_zip = ? ORDER BY hotel_id LIMIT 1",
                (zip_code,),
            ).fetchone()
            rows = connection.execute(
                "SELECT h.* FROM saved_hotels h JOIN saved_hotel_locations l "
                "ON h.hotel_id = l.hotel_id WHERE l.requested_zip = ? ORDER BY h.hotel_id",
                (zip_code,),
            ).fetchall()
            return SavedHotelSearchResponse(
                search_center=SavedSearchCenter(**dict(context)) if context else None,
                hotels=[self._saved_hotel(connection, row) for row in rows],
            )

    def saved_hotel_ids(self, place_ids: List[str]) -> List[str]:
        """Check identity globally, even if saved under a different ZIP."""
        if not place_ids:
            return []
        placeholders = ", ".join("?" for _ in place_ids)
        with self.open() as connection:
            rows = connection.execute(
                f"SELECT hotel_id FROM saved_hotels WHERE hotel_id IN ({placeholders}) ORDER BY hotel_id",
                tuple(place_ids),
            ).fetchall()
        return [row["hotel_id"] for row in rows]

    def delete_saved_hotel(self, place_id: str) -> None:
        """Atomically remove one saved identity, all its ZIP contexts and nights."""
        with self.open() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM saved_hotel_locations WHERE hotel_id = ?", (place_id,))
            connection.execute("DELETE FROM demo_hotel_nights WHERE hotel_id = ?", (place_id,))
            cursor = connection.execute("DELETE FROM saved_hotels WHERE hotel_id = ?", (place_id,))
            if cursor.rowcount == 0:
                raise KeyError(place_id)
