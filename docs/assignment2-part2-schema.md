# Assignment 2 Part 2: saved hotel schema

Database: `backend/expedia.sqlite3`. `DatabaseController.initialize()` applies the additive migration with `CREATE TABLE IF NOT EXISTS`, for both existing and fresh databases. Repeating it preserves records. The Assignment 1 tables and CSV seeding rules remain unchanged.

## API field mapping

| `saved_hotels` column | Part 1 API field | Rule |
| --- | --- | --- |
| `hotel_id` | `place_id` | Required text primary key; copy the provider ID exactly, without trimming, case changes, or numeric conversion. Duplicate IDs are rejected. |
| `name` | `name` | Nullable when the provider name is missing. Part 1's `Name unavailable` is a display fallback, not a provider name to invent in storage. |
| `address` | `formatted_address` | Nullable when missing. |
| `latitude` | `latitude` | Required numeric value from -90 to 90. |
| `longitude` | `longitude` | Required numeric value from -180 to 180. |

The save endpoint accepts the existing Part 1 hotel fields and search center. The known `Name unavailable` fallback and blank names are stored as NULL; the frozen Part 1 response itself is unchanged. Saving the same ID again retains the original hotel fields.

## Daily classroom data

`demo_hotel_nights` uses `(hotel_id, stay_date)` as its primary key. Its required `hotel_id` references `saved_hotels`; foreign keys are enabled on every controller connection and deleting a hotel with stored nights is restricted. DB Explorer connections must also enable `PRAGMA foreign_keys = ON` before editing.

`stay_date` must be a valid calendar date in `YYYY-MM-DD` format. `nightly_rate_cents` is a nonnegative integer with default **10000 ($100.00)**; `rooms_available` is a nonnegative integer with default **20**. These values are **fictional classroom defaults**, not Geoapify prices or availability. Defaults apply when a night row is inserted without these values; the migration creates no hotel or night records.

Each successful save inserts any missing nights for **October 10–14, 2026 (inclusive)**. Existing nights, rates, and room counts are never overwritten. No price or room count is accepted from the save request.

## ZIP association and controller methods

`saved_hotel_locations` stores each hotel's searched ZIP, matching resolved postcode, optional city/state, and postcode coordinates, keyed by `(hotel_id, requested_zip)`. It references `saved_hotels`. ZIPs remain five-digit text, including leading zeros. Repeated associations keep their original context; a hotel can be associated with several ZIPs. A local ZIP response uses the stored context of the first hotel ordered by provider ID.

`SavedHotelController` validates ZIP input and applies classroom-date/name rules. It calls the public `DatabaseController` methods `save_api_hotel(hotel, center, stay_dates)`, `get_saved_hotels(zip_code)`, `saved_hotel_ids(place_ids)`, and `delete_saved_hotel(place_id)`. Models define DTO fields in `backend/models/saved_hotels.py`; only the database controller owns SQL. Save and removal each use one transaction.

## HTTP and View contract

| Endpoint | Contract |
| --- | --- |
| `POST /api/saved-hotels` | Body: `{"hotel": {"place_id": "provider ID", "name": null, "formatted_address": null, "latitude": 42.36, "longitude": -71.06}, "search_center": {"requested_zip": "02108", "resolved_postcode": "02108", "city": "Boston", "state": "MA", "latitude": 42.357, "longitude": -71.065}}`. Returns `200` with `{"saved": true, "hotel": <stored hotel with demo_nights>}`; repeated saves are safe. |
| `GET /api/saved-hotels?zip=02108` | Returns `{"search_center": <stored center>, "hotels": [...]}`. Each hotel has the Part 1 field names (nullable name/address) plus `demo_nights`, containing `stay_date`, `nightly_rate_cents`, and `rooms_available`. Empty success is `{"search_center": null, "hotels": []}`. |
| `GET /api/saved-hotels/status?place_id=<ID>` | Repeat `place_id` to check up to 100 IDs. Returns `{"saved_ids": [...]}` from the database, independent of the searched ZIP. |
| `DELETE /api/saved-hotels?place_id=<ID>` | Removes that hotel, all its ZIP associations, and all its demo nights atomically. Returns `{"place_id": "<ID>", "removed": true}`. Other hotels and Assignment 1 records remain unchanged. |

IDs are URL-encoded query values so opaque IDs containing slashes, spaces, or punctuation remain intact. Invalid input is `422`, removal of an unsaved ID is `404`, and a storage-operation failure is a safe `503`; raw database errors are not returned.

Vue requests local hotels first. Nonempty success shows **Saved locally**, stored map/list context, and dated rates/rooms labelled **Simulated classroom data**. Only an empty success calls frozen `/api/live-hotels` and shows **API results**. A local error stops lookup. API results get saved status by provider ID from the database, including on a new search after refreshing the page; browser localStorage is not the source of truth.

Add is disabled for saved or pending hotels. Remove is offered only for saved hotels. Status/results change only after a successful acknowledgment; failures show feedback and preserve the current display. Local removal clears the matching row/marker and selected ID if needed. Removing the last local hotel does not automatically call the provider: search again to check API results. Local saved results are explicitly not a complete nearby hotel inventory. Selection buttons, keyboard focus, map attribution, and the Assignment 1 flow remain separate from these actions.

Checks: the backend suite uses temporary databases for mutations; frontend HTTP workflow tests run with Node's built-in test runner (`node --test frontend/tests/local-hotels.test.js` from the repository root), with mocked fetch responses and no extra dependency.

Initialization runs when the backend first serves a database-backed request. To apply it directly from the project root on macOS/Linux:

```sh
backend/.venv/bin/python -c "from pathlib import Path; from backend.controllers.database import DatabaseController; DatabaseController(Path('backend/expedia.sqlite3')).initialize()"
```
