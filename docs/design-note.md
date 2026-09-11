# Part 1 design note

The Vue frontend is responsible for collecting a hotel name, sending the search request, and presenting either a readable table of matching stays or a clear no-results message.

FastAPI provides the HTTP endpoint that accepts the hotel-name query and returns JSON results to Vue. The Python backend is responsible for reading only `hotels.csv` and `trips.csv`, filtering hotels by name, and shaping the matching stay records.

The backend joins `hotels.csv` and `trips.csv` using `hotel_id`. The application flow is:

1. The user enters a hotel name and selects Search.
2. Vue sends the name to the FastAPI endpoint.
3. Python finds matching hotels and connects their trips by `hotel_id`.
4. FastAPI returns the available stays.
5. Vue displays the results table or the no-results message.
