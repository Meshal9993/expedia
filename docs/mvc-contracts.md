# MVC contracts

## Models and relationships

The four instructor CSVs define these models. IDs are text identifiers, not generated database integers.

| Model | Fields | Relationship |
| --- | --- | --- |
| Hotel | `hotel_id`, `hotel_name`, `city`, `state`, `nightly_rate_usd` | `hotel_id` is primary key |
| Trip | `trip_id`, `hotel_id`, `trip_name`, `check_in`, `check_out` | `trip_id` is primary key; `hotel_id` references Hotel |
| User | `user_id`, `display_name` | `user_id` is primary key |
| Booking | `booking_id`, `user_id`, `trip_id`, `booked_on`, `status` | `booking_id` is primary key; `user_id` references User; `trip_id` references Trip |

`backend/models/entities.py` defines immutable entity objects. `HotelStay` is a read-only search-result model joining Hotel and Trip. Date fields are ISO `YYYY-MM-DD` strings; `nightly_rate_usd` is numeric.

## Controller contracts

`DatabaseController(path)` owns SQLite connections, schema, first-time CSV import, and foreign-key enforcement. `initialize()` creates the schema, imports the four CSVs once, and checks references. `check_references()` raises `ValueError` if stored references are invalid. Each CRUD call uses a fresh connection with foreign keys enabled:

- `create(entity) -> entity`
- `get(Model, id) -> entity`
- `list(Model) -> list[entity]`
- `update(entity) -> entity`
- `delete(Model, id) -> None`

`get`, `update`, and `delete` raise `KeyError` for a missing ID. Duplicate IDs and invalid references raise `sqlite3.IntegrityError`. Deleting a referenced hotel, trip, or user is rejected. These CRUD methods are backend-only for now; they are not public HTTP endpoints.

`SearchController` accepts a `DatabaseController`. Its `search_hotels(name)` method trims the name, returns `{"results": []}` for blank input, and otherwise requests matching Hotel/Trip rows through the database controller. Controllers communicate through these public methods, not each other's SQL or private functions.

`BookingController` owns booking-specific rules and uses only the public `DatabaseController` CRUD contract. It generates the next available `B`-prefixed numeric ID, validates that the traveler and trip exist, creates bookings with `confirmed` status, assembles booking history details, changes cancellation status without deleting the record, and deletes an explicitly requested booking. It raises `BookingReferenceError` for an unknown traveler or trip and `BookingNotFoundError` for an unknown booking.

## View and HTTP contract

Vue components and CSS in `frontend/` own input, loading and error states, table rendering, and presentation formatting. They do not read CSVs or SQLite. FastAPI in `backend/main.py` is the HTTP adapter.

`GET /api/hotels?name=<hotel-name>` accepts a text hotel name and returns JSON with a `results` array. Search is case-insensitive and matches a hotel-name substring. Each result has `hotel_id`, `hotel_name`, `city`, `state`, numeric `nightly_rate_usd`, `trip_id`, `trip_name`, `check_in`, and `check_out`. A blank or unmatched name returns an empty array; the View chooses the message to show.

## Booking API contract

Booking-detail responses use this shape:

```json
{
  "booking": {
    "booking_id": "B007",
    "user_id": "U001",
    "trip_id": "T001",
    "booked_on": "2026-09-21",
    "status": "confirmed"
  },
  "traveler": {"user_id": "U001", "display_name": "Demo Traveler 1"},
  "trip": {
    "trip_id": "T001",
    "hotel_id": "H001",
    "trip_name": "Boston Harbor Weekend",
    "check_in": "2026-09-18",
    "check_out": "2026-09-20"
  },
  "hotel": {
    "hotel_id": "H001",
    "hotel_name": "Harbor Lantern Hotel",
    "city": "Boston",
    "state": "MA",
    "nightly_rate_usd": 150.0
  }
}
```

### `POST /api/bookings`

Request:

```json
{"user_id": "U001", "trip_id": "T001", "booked_on": "2026-09-21"}
```

The API generates `booking_id`, forces the initial status to `confirmed`, saves the booking, and returns the booking-detail shape with `201 Created`. An unknown `user_id` or `trip_id` returns `404` with `{"detail": "... was not found"}`. Invalid or missing request fields return FastAPI's `422` validation response.

### `GET /api/bookings`

Returns `200` and `{"bookings": [<booking-detail>, ...]}`. The optional `user_id` query parameter filters history for one traveler, for example `GET /api/bookings?user_id=U001`. An unknown filter ID returns `404`.

### `GET /api/bookings/{booking_id}`

Returns one booking-detail object with `200`. A missing booking returns `404` with `{"detail": "Booking '...' was not found"}`.

### `PATCH /api/bookings/{booking_id}`

Request:

```json
{"status": "cancelled"}
```

Returns the updated booking-detail object with `200`. Cancellation retains the row and changes only its status. `cancelled` is the only supported status input; another value returns `422`. A missing booking returns `404`.

### `DELETE /api/bookings/{booking_id}`

Returns `200` and `{"booking_id": "B007", "deleted": true}`. A missing booking returns `404`. This operation is intended for explicitly selected test bookings; cancellation uses `PATCH`, not deletion.
