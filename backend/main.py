"""HTTP boundary between the Vue view and backend controllers."""

from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.controllers.booking import (
    BookingController,
    BookingNotFoundError,
    BookingReferenceError,
)
from backend.controllers.database import DatabaseController
from backend.controllers.search import SearchController
from backend.models.api import BookingCreateRequest, BookingUpdateRequest


DATABASE_PATH = Path(__file__).parent / "expedia.sqlite3"

app = FastAPI(title="Expedia API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@lru_cache
def get_database() -> DatabaseController:
    database = DatabaseController(DATABASE_PATH)
    database.initialize()
    return database


def get_booking_controller(
    database: DatabaseController = Depends(get_database),
) -> BookingController:
    return BookingController(database)


@app.exception_handler(BookingNotFoundError)
def booking_not_found_handler(_, error: BookingNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.exception_handler(BookingReferenceError)
def booking_reference_handler(_, error: BookingReferenceError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.get("/api/hotels")
def search_hotels(
    name: str = Query(default=""),
    database: DatabaseController = Depends(get_database),
) -> dict[str, object]:
    return SearchController(database).search_hotels(name)


@app.post("/api/bookings", status_code=201)
def create_booking(
    request: BookingCreateRequest,
    controller: BookingController = Depends(get_booking_controller),
) -> dict[str, object]:
    return controller.create_booking(
        request.user_id,
        request.trip_id,
        request.booked_on,
    )


@app.get("/api/bookings")
def get_booking_history(
    user_id: str | None = Query(default=None),
    controller: BookingController = Depends(get_booking_controller),
) -> dict[str, object]:
    return {"bookings": controller.get_history(user_id)}


@app.get("/api/bookings/{booking_id}")
def get_booking(
    booking_id: str,
    controller: BookingController = Depends(get_booking_controller),
) -> dict[str, object]:
    return controller.get_booking(booking_id)


@app.patch("/api/bookings/{booking_id}")
def update_booking(
    booking_id: str,
    _: BookingUpdateRequest,
    controller: BookingController = Depends(get_booking_controller),
) -> dict[str, object]:
    return controller.cancel_booking(booking_id)


@app.delete("/api/bookings/{booking_id}")
def delete_booking(
    booking_id: str,
    controller: BookingController = Depends(get_booking_controller),
) -> dict[str, object]:
    return controller.delete_booking(booking_id)
