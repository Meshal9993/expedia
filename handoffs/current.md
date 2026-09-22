# Current handoff

## What currently works

- The Vue frontend searches by hotel name and displays matching hotels and available stays in a labeled table.
- A user can select a stay, choose one of six supplied demo travelers, and create a confirmed booking.
- Booking History shows booking, traveler, hotel, stay, date, and status details and can be filtered by traveler.
- A confirmed booking can be cancelled while remaining visible as `Cancelled`.
- A separately selected temporary test booking can be deleted after confirmation.
- Clear loading, success, error, empty-history, and no-results states are present.

## MVC architecture and persistence

- Model entities and relationships are defined in `backend/models/`.
- `DatabaseController` exclusively owns SQLite connections, SQL, schema creation, first-time CSV seeding, foreign-key enforcement, and CRUD.
- `SearchController` and `BookingController` own their respective business rules and use the database controller's public contract.
- FastAPI routes remain thin HTTP adapters, and the Vue View communicates only through the documented JSON API.
- The generated `backend/expedia.sqlite3` database is ignored by Git. It seeds the four supplied CSVs once, preserves their IDs, and does not reseed an initialized database.
- Search, booking creation, history, cancellation, and deletion read and write SQLite after initial seeding; no changes are written back to CSV.

## Final verification

Manual browser review completed:

- Searching for `Harbor Lantern Hotel` displayed Boston Harbor Weekend and Boston Autumn Weekend.
- Booking `B007` appeared in Booking History after an application restart.
- Cancelling `B007` through the frontend retained it with status `Cancelled`.
- After a browser refresh, `B007` was still visible as `Cancelled`.
- A separate temporary test booking was created and deleted through the frontend; it disappeared from history after the API confirmed deletion.
- Searching for `IST402` displayed the no-results state.
- The interface was visually reviewed at normal desktop width and at a narrower width.

Automated verification completed:

- The full backend suite passed with 16 tests covering seeding, relationships, SQLite CRUD and persistence, hotel search, booking rules, and HTTP behavior.
- Frontend lint and the production build passed.
- Restart verification preserved the database counts and booking `B007`; starter records were not duplicated.
- `git diff --check` passed.
- The instructor CSV files remained unchanged.

Manual evidence is stored in `docs/screenshots/`.

## Current limitations

- The application uses supplied demo travelers and has no authentication or authorization.
- Payments, surge pricing, and real Expedia integrations are outside this project's scope.
- Persistence is a local SQLite database intended for this single-project demonstration.
- Delete remains available for explicitly selected temporary test bookings; ordinary cancellation retains the booking.
- The Part 2 final report has not been written, and the feature branch has not yet been committed or merged.

## Next task

Perform the final Git diff review, commit the completed Part 2 work, and merge the feature branch according to the submission workflow.
