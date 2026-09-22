# Part 2 booking controller and API

Continue on `feature/part2-mvc-crud` and follow the repository MVC contracts. Keep SQLite CRUD and reference enforcement in `DatabaseController`; put booking-specific business rules in a new `BookingController`; keep FastAPI routes thin; and do not change Vue or the instructor CSVs.

Implement booking creation using existing traveler and trip IDs, a generated unique booking ID, the supplied booking date, and an initial `confirmed` status. Reject unknown references cleanly. Return booking history, optionally filtered by `user_id`, with booking, traveler, trip, and hotel details. Support retrieving one booking, cancelling it by retaining the row and setting its status to `cancelled`, and deleting an explicitly selected test booking with clear missing-booking behavior.

Expose and document these JSON endpoints:

- `POST /api/bookings`
- `GET /api/bookings`
- `GET /api/bookings/{booking_id}`
- `PATCH /api/bookings/{booking_id}`
- `DELETE /api/bookings/{booking_id}`

Use appropriate HTTP status codes and controller-level errors. Add backend tests for creation, invalid user and trip references, full and user-filtered history, single retrieval, retained cancellation, deletion, missing bookings, reopening persistence, and the full HTTP lifecycle. Preserve Part 1 hotel search. Do not add authentication, payments, surge pricing, or real Expedia integrations. Do not commit until reviewed.
