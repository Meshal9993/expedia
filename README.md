# Expedia Project

This repository is an Expedia-style travel application. It keeps the FastAPI backend and Vue frontend separate while preserving the instructor-supplied CSV data as read-only source data.

Repository: [Meshal9993/expedia](https://github.com/Meshal9993/expedia). The [Assignment 2 Part 1 report](report.md) assesses implementation commit `85d0ac345a451267742c456a3d1ee70e524e3f72`. The report was published separately in `49962a4f0b4d4d368233cfa851f65d470b2881b8`.

## Project layout

```text
expedia/
|-- backend/             # FastAPI routes, models, controllers, and CSV data
|   |-- controllers/     # SQLite CRUD, booking rules, and hotel-search logic
|   |-- models/          # Booking entities and separate live-place DTOs
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

## Assignment 1 Part 2 behavior

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

On macOS or Linux, use the equivalent commands from the project root:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m uvicorn backend.main:app --reload
```

Start the API from the project root:

```powershell
backend/.venv/Scripts/python.exe -m uvicorn backend.main:app --reload
```

The API is then available at `http://127.0.0.1:8000`.

If the local environment blocks file watching, omit `--reload` on macOS/Linux:

```sh
backend/.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

With this command, restart the backend after changing Python source files.

Hotel search is available at `GET /api/hotels?name=<hotel-name>`. Booking endpoints are available at `POST /api/bookings`, `GET /api/bookings`, `GET /api/bookings/{booking_id}`, `PATCH /api/bookings/{booking_id}`, and `DELETE /api/bookings/{booking_id}`. See `docs/mvc-contracts.md` for their JSON contracts.

The separate Assignment 2 backend endpoint `GET /api/live-hotels?zip=16801` returns a matching U.S. postcode center and up to 20 Geoapify hotel places within 5 km. It reports place locations, not room availability or booking prices. To enable it, create local `backend/.env` and add a `GEOAPIFY_API_KEY` setting with your local key, or set the process environment variable. `backend/.env` is ignored by Git and the key stays on the backend. Changes to `backend/.env` are read on the next request; restart the backend after changing its process environment. The Vue Live Hotel Search section uses this endpoint for its list and Leaflet map. See `docs/assignment2-part1-contracts.md` for response and error details.

On first use, the backend creates the ignored local database `backend/expedia.sqlite3` and imports the four read-only CSV files. Later CRUD changes persist in SQLite and do not alter the CSVs. Delete the local database only if you intentionally want to recreate it from the CSVs; this loses local database changes.

Assignment 2 Part 2 adds `saved_hotels`, `demo_hotel_nights`, and separate ZIP/location associations through repeatable database initialization. `POST /api/saved-hotels` saves a hotel/context and missing demo nights for October 10–14, 2026; `GET /api/saved-hotels?zip=<ZIP>` retrieves local matches. Status is checked by provider ID, and `DELETE /api/saved-hotels?place_id=<ID>` removes a hotel, its associations, and nights together. Repeated saves preserve existing rates/rooms. Defaults of $100.00 and 20 rooms are fictional classroom data, not provider information. See the [schema, API, and View contracts](docs/assignment2-part2-schema.md) for details.

Backend checks:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests
```

On macOS or Linux, run `backend/.venv/bin/python -m pytest backend/tests`.

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

The frontend defaults to the FastAPI service at `http://127.0.0.1:8000`; `VITE_API_BASE_URL` can override that backend address when starting Vite. Live Hotel Search accepts a five-digit ZIP string and keeps the hotel list and Leaflet markers synchronized. OpenStreetMap supplies public map tiles, with its attribution visible; no Geoapify key is needed in Vue. The separate Local demo bookings section retains hotel-name search and SQLite booking behavior. See `docs/mvc-contracts.md` for the original API and `docs/assignment2-part1-contracts.md` for live-search contracts. Treat `backend/data/*.csv` as read-only instructor data throughout development.

ZIP lookup now checks saved hotels first; only an empty local success calls the unchanged Part 1 API. Results are labelled **Saved locally** or **API results**. Add/Remove buttons reflect database status after a search, including after refresh. Local nightly values are dated and labelled **Simulated classroom data**; saved results are not a complete list of nearby hotels. Frontend HTTP checks: `node --test frontend/tests/local-hotels.test.js` from the project root.

## Assignment 2, Part 1 evidence

The implementation and final simplified interface were verified on September 30, 2026: live `16801`, leading-zero `02108`, invalid `1234`, both selection directions, and the original `Harbor Lantern Hotel` search passed. Frontend lint/build and all 40 backend tests passed. Empty, unresolved, service-failure, and rate-limit cases were checked with mocks; counts are live observations, not fixed test expectations.

The [final report](report.md) and [evidence log](docs/assignment2-part1-evidence.md) describe the completed work, retained demo video, revised approaches, AI disclosure, and limitations. Part 1 media is video-only at the student's request. See also the [research](docs/assignment2-part1-research.md), [early mockup](docs/assignment2-part1-mockup.md), [contracts](docs/assignment2-part1-contracts.md), and [current handoff](handoffs/current.md).
