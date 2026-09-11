# Part 1 hotel search

Implement a simple Vue and FastAPI hotel search. Provide one hotel-name input and a Search button. Display matching hotels and their available stays in a readable table, with a clear message when nothing matches.

The Python backend must read only `backend/data/hotels.csv` and `backend/data/trips.csv`, join them using `hotel_id`, search by hotel name, and return matching records to Vue. Do not use users or bookings data, SQLite, booking features, new dependencies, or modified CSV files. Verify one successful search and one no-results search without committing the implementation.
