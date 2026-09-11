# Expedia Project

This repository is the starting structure for an Expedia-style travel application. It keeps the future FastAPI backend and Vue frontend separate while preserving the instructor-supplied CSV data as read-only source data.

## Project layout

```text
expedia/
|-- backend/             # Future Python and FastAPI work
|   `-- data/            # Instructor-supplied CSV files
|-- frontend/            # Future Vue work
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

## Development setup

The development environments are kept separate. Python dependencies belong only in `backend/.venv`, and frontend dependencies belong only in `frontend/node_modules`.

### Backend

Python 3.10 or newer is required. From the project root on Windows PowerShell:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
```

Use `backend/.venv/Scripts/python.exe` for backend commands so packages are never installed globally.

### Frontend

The frontend uses Vue with Vite and ESLint. From the project root:

```powershell
Set-Location frontend
npm install
npm run dev
```

Quality checks:

```powershell
npm run lint
npm run build
```

Application-specific backend and frontend run commands will be added after their entry points are implemented. Treat `backend/data/*.csv` as read-only instructor data throughout development.
