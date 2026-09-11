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

## Setup status

This is a structure-only scaffold. No application code or dependency manifests have been created, and no dependencies have been installed.

To begin working with the scaffold:

1. Open a terminal in the existing `expedia` directory.
2. Use `backend/` for future Python and FastAPI code.
3. Use `frontend/` for future Vue code.
4. Treat `backend/data/*.csv` as read-only instructor data.

Backend and frontend installation and run commands should be documented here after their dependency manifests and application entry points are created.
