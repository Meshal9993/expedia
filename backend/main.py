import csv
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware


DATA_DIRECTORY = Path(__file__).parent / "data"

app = FastAPI(title="Expedia Hotel Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def read_csv(filename: str) -> list[dict[str, str]]:
    with (DATA_DIRECTORY / filename).open(encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


@app.get("/api/hotels")
def search_hotels(name: str = Query(default="")) -> dict[str, object]:
    normalized_name = name.strip().casefold()
    if not normalized_name:
        return {"results": []}

    hotels = {
        hotel["hotel_id"]: hotel
        for hotel in read_csv("hotels.csv")
        if normalized_name in hotel["hotel_name"].casefold()
    }

    results = []
    for trip in read_csv("trips.csv"):
        hotel = hotels.get(trip["hotel_id"])
        if hotel is None:
            continue

        results.append(
            {
                "hotel_id": hotel["hotel_id"],
                "hotel_name": hotel["hotel_name"],
                "city": hotel["city"],
                "state": hotel["state"],
                "nightly_rate_usd": float(hotel["nightly_rate_usd"]),
                "trip_id": trip["trip_id"],
                "trip_name": trip["trip_name"],
                "check_in": trip["check_in"],
                "check_out": trip["check_out"],
            }
        )

    return {"results": results}
