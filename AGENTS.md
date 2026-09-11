# Project Rules

These rules apply to the entire repository.

## Architecture

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

## Development

- Add backend dependencies only to backend-specific dependency files.
- Add frontend dependencies only to frontend-specific dependency files.
- Do not commit virtual environments, installed packages, build output, caches, secrets, or local environment files.
- Document setup and run commands in the root `README.md` when application code and dependency manifests are introduced.
- Keep changes focused, and verify the relevant backend or frontend checks before handing off work.
