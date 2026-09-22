# Expedia Project

This repository is an Expedia-style travel application. It keeps the FastAPI backend and Vue frontend separate while preserving the instructor-supplied CSV data as read-only source data.

## Project layout

```text
expedia/
|-- backend/             # FastAPI routes, models, controllers, and CSV data
|   |-- controllers/     # SQLite CRUD, booking rules, and hotel-search logic
|   |-- models/          # Hotel, trip, user, and booking entities
|   `-- data/            # Instructor-supplied CSV files (read-only)
|-- frontend/            # Vue View and CSS
|-- docs/                # Project documentation
|-- prompts/             # Saved project prompts
|-- handoffs/            # Team handoff notes
|-- AGENTS.md             # Repository working rules
`-- README.md             # Project overview and setup
```

## Supplied data

The files in `backend/data/` are the original instructor data and must not be modified:

| File | Columns | Records |
| --- | --- | ---: |
| `hotels.csv` | `hotel_id`, `hotel_name`, `city`, `state`, `nightly_rate_usd` | 8 |
| `trips.csv` | `trip_id`, `hotel_id`, `trip_name`, `check_in`, `check_out` | 12 |
| `users.csv` | `user_id`, `display_name` | 6 |
| `bookings.csv` | `booking_id`, `user_id`, `trip_id`, `booked_on`, `status` | 6 |

The relationships are:

- `trips.hotel_id` references `hotels.hotel_id`.
- `bookings.user_id` references `users.user_id`.
- `bookings.trip_id` references `trips.trip_id`.
- `booking_id`, `user_id`, `trip_id`, and `hotel_id` are the identifiers for their respective records.

## Current Part 2 behavior

- Hotel-name search returns matching hotels and available stays from SQLite.
- A user can select a stay and create a confirmed booking for one of the six supplied demo travelers.
- Booking History displays traveler, hotel, stay, dates, and status, with an optional traveler filter.
- Cancelling changes a booking's status to `cancelled` and retains the record.
- Deleting is a separate, confirmed action intended for temporary test bookings.
- SQLite changes persist across backend and frontend restarts. The instructor CSV files remain unchanged and are used only for first-time database seeding.

The project follows MVC boundaries: immutable entities in `backend/models/` define the Model, Vue and CSS in `frontend/` provide the View, and controllers in `backend/controllers/` own persistence and business rules. FastAPI routes are thin HTTP adapters between the View and controllers. The exact contracts are documented in `docs/mvc-contracts.md`.

## Development setup

The development environments are kept separate. Python dependencies belong only in `backend/.venv`, and frontend dependencies belong only in `frontend/node_modules`.

### Backend

Python 3.10 or newer is required. From the project root on Windows PowerShell:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
```

Use `backend/.venv/Scripts/python.exe` for backend commands so packages are never installed globally.

Start the API from the project root:

```powershell
backend/.venv/Scripts/python.exe -m uvicorn backend.main:app --reload
```

The API is then available at `http://127.0.0.1:8000`.

Hotel search is available at `GET /api/hotels?name=<hotel-name>`. Booking endpoints are available at `POST /api/bookings`, `GET /api/bookings`, `GET /api/bookings/{booking_id}`, `PATCH /api/bookings/{booking_id}`, and `DELETE /api/bookings/{booking_id}`. See `docs/mvc-contracts.md` for their JSON contracts.

On first use, the backend creates the ignored local database `backend/expedia.sqlite3` and imports the four read-only CSV files. Later CRUD changes persist in SQLite and do not alter the CSVs. Delete the local database only if you intentionally want to recreate it from the CSVs; this loses local database changes.

Backend checks:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests
```

### Frontend

The frontend uses Vue with Vite and ESLint. From the project root:

```powershell
Set-Location frontend
npm install
npm run dev
```

Vite displays the local URL when it starts; with the default configuration, open `http://127.0.0.1:5173/`.

Quality checks:

```powershell
npm run lint
npm run build
```

The frontend sends hotel-name searches to the FastAPI service. See `docs/mvc-contracts.md` for MVC responsibilities, model relationships, and HTTP contracts. Treat `backend/data/*.csv` as read-only instructor data throughout development.
