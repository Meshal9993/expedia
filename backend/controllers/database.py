"""SQLite persistence for the four instructor-supplied entities."""

import csv
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

from backend.models.entities import Booking, Hotel, HotelStay, Trip, User


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
        """Create schema and import the read-only CSVs once for a new database."""
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

    def search_hotel_stays(self, name: str) -> list[HotelStay]:
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
