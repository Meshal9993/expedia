# Project Rules

These rules apply to the entire repository.

## Architecture

- Follow Model–View–Controller (MVC) boundaries:
  - Model: define entity fields and relationships in `backend/models/`. Models do not read files, query SQLite, or render UI.
  - View: keep screens, components, state presentation, and CSS in `frontend/`. The View calls the documented HTTP API and never opens the database or imports Python.
  - Controller: keep SQLite access and CRUD in `backend/controllers/database.py`; keep other business logic in separate modules under `backend/controllers/`. FastAPI routes in `backend/main.py` translate HTTP requests and responses, then call controllers.
- Respect the contracts in `docs/mvc-contracts.md`: model instances in and out of database CRUD, documented controller methods between controllers, and JSON over HTTP between backend and View. Do not couple layers through private functions or shared mutable state.
- Controllers may call other controllers through their documented public methods. Only the database controller owns SQL and CSV import.
- Keep Python and FastAPI code in `backend/`.
- Keep Vue code in `frontend/`.
- Keep backend and frontend responsibilities separate. Communicate across a documented HTTP API rather than importing code across the two directories.
- Put shared project documentation in `docs/`, reusable prompts in `prompts/`, and handoff notes in `handoffs/`.
- Do not create another nested `expedia/` directory.

## Data

- Treat every CSV file in `backend/data/` as instructor-supplied, read-only source data.
- Do not rename, edit, reformat, regenerate, or overwrite the supplied CSV files.
- Do not place generated output in `backend/data/`.
- Preserve the existing ID relationships among hotels, trips, users, and bookings.
- Seed a local SQLite database from the CSVs only when it is first created. Never write database changes back to the instructor CSVs.

## Development

- Add backend dependencies only to backend-specific dependency files.
- Add frontend dependencies only to frontend-specific dependency files.
- Do not commit virtual environments, installed packages, build output, caches, secrets, or local environment files.
- Document setup and run commands in the root `README.md` when application code and dependency manifests are introduced.
- Keep changes focused, and verify the relevant backend or frontend checks before handing off work.

## Assignment 2 live hotel search

- Preserve MVC boundaries: model provider-backed data in `backend/models/`, keep Geoapify calls and validation in a backend controller, keep FastAPI routes thin, and let Vue consume only the documented JSON API.
- Represent provider data honestly. Never invent hotel price, rating, room availability, or booking information, and do not treat live places as the instructor-supplied bookable Hotel/Trip records.
- Keep `GEOAPIFY_API_KEY` server-side in ignored `backend/.env`; never place it in frontend code, responses, or logs.
- Preserve ZIP codes as five-digit strings, including leading zeros. Distinguish a successful empty Places result from an unresolved ZIP, provider failure, and rate-limit or quota failure.
- Before adding dependencies, follow **CHECK → TAKE ACTION → VERIFY**: inspect existing manifests and installed capabilities, obtain approval for any needed installation or declaration, then verify the intended environment.
