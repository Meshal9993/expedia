"""HTTP boundary between the Vue view and backend controllers."""

from functools import lru_cache
from pathlib import Path
from uuid import UUID

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from backend.controllers.chat import ChatConfigurationError, ChatController
from backend.models.chat import ChatRequest
from backend.controllers.hotel_chat import HotelChatController, HotelChatError
from backend.models.hotel_chat import ChatHistory, HotelChatRequest, HotelChatResponse

from backend.controllers.booking import (
    BookingController,
    BookingNotFoundError,
    BookingReferenceError,
)
from backend.controllers.database import DatabaseController
from backend.controllers.location import (
    InvalidZipError,
    LocationConfigurationError,
    LocationController,
    LocationError,
    ProviderFailureError,
    ProviderRateLimitError,
    UnresolvedZipError,
)
from backend.controllers.search import SearchController
from backend.controllers.saved_hotels import (
    LocalStorageError, SavedHotelController, SavedHotelNotFoundError,
)
from backend.models.api import BookingCreateRequest, BookingUpdateRequest
from backend.models.live_hotels import LiveHotelSearchResponse
from backend.models.saved_hotels import (
    RemoveHotelResponse, SaveHotelRequest, SaveHotelResponse,
    SavedHotelSearchResponse, SavedHotelStatusResponse,
)


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


def get_location_controller() -> LocationController:
    return LocationController()


def get_chat_controller() -> ChatController:
    return ChatController()


def get_hotel_chat_controller(
    database: DatabaseController = Depends(get_database),
    model: ChatController = Depends(get_chat_controller),
) -> HotelChatController:
    return HotelChatController(database, model)


def get_saved_hotel_controller(
    database: DatabaseController = Depends(get_database),
) -> SavedHotelController:
    return SavedHotelController(database)


LOCATION_ERROR_RESPONSES = {
    InvalidZipError: (422, "Enter exactly five digits for a U.S. ZIP code."),
    UnresolvedZipError: (404, "ZIP code could not be resolved."),
    ProviderRateLimitError: (429, "Hotel searches are temporarily limited. Try again later."),
    ProviderFailureError: (502, "Hotel search service is unavailable. Try again later."),
    LocationConfigurationError: (503, "Hotel search service is not configured."),
}


@app.exception_handler(LocationError)
def location_error_handler(_, error: LocationError) -> JSONResponse:
    status_code, detail = LOCATION_ERROR_RESPONSES[type(error)]
    return JSONResponse(status_code=status_code, content={"detail": detail})


@app.exception_handler(BookingNotFoundError)
def booking_not_found_handler(_, error: BookingNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.exception_handler(LocalStorageError)
def local_storage_error_handler(_, __) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "Local hotel storage is unavailable. Try again later."})


@app.exception_handler(SavedHotelNotFoundError)
def saved_hotel_not_found_handler(_, __) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Hotel is not saved locally."})


@app.exception_handler(BookingReferenceError)
def booking_reference_handler(_, error: BookingReferenceError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.exception_handler(ChatConfigurationError)
def chat_configuration_handler(_, __) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "Chat service is not configured."})


@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    controller: ChatController = Depends(get_chat_controller),
) -> StreamingResponse:
    controller.ensure_configured()

    async def events():
        async for event in controller.stream_reply(request):
            yield event.model_dump_json(exclude_none=True) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson", headers={"Cache-Control": "no-store"})


@app.exception_handler(HotelChatError)
def hotel_chat_error_handler(_, error: HotelChatError) -> JSONResponse:
    content = {"code": error.code, "detail": error.detail}
    if error.conversation_id:
        content["conversation_id"] = str(error.conversation_id)
    return JSONResponse(status_code=error.status, content=content, headers={"Cache-Control": "no-store"})


@app.post("/api/hotel-chat", response_model=HotelChatResponse)
async def hotel_chat(
    request: HotelChatRequest, controller: HotelChatController = Depends(get_hotel_chat_controller),
) -> HotelChatResponse:
    return await controller.ask(request)


@app.get("/api/hotel-chat/{conversation_id}", response_model=ChatHistory)
def hotel_chat_history(
    conversation_id: UUID, controller: HotelChatController = Depends(get_hotel_chat_controller),
) -> ChatHistory:
    return controller.history(conversation_id)


@app.get("/api/hotels")
def search_hotels(
    name: str = Query(default=""),
    database: DatabaseController = Depends(get_database),
) -> dict[str, object]:
    return SearchController(database).search_hotels(name)


@app.get(
    "/api/live-hotels",
    response_model=LiveHotelSearchResponse,
    response_model_exclude_none=True,
)
def search_live_hotels(
    zip_code: str = Query(default="", alias="zip"),
    controller: LocationController = Depends(get_location_controller),
) -> LiveHotelSearchResponse:
    return controller.search_live_hotels(zip_code)


@app.get("/api/saved-hotels", response_model=SavedHotelSearchResponse)
def search_saved_hotels(
    zip_code: str = Query(default="", alias="zip"),
    controller: SavedHotelController = Depends(get_saved_hotel_controller),
) -> SavedHotelSearchResponse:
    return controller.search(zip_code)


@app.get("/api/saved-hotels/status", response_model=SavedHotelStatusResponse)
def saved_hotel_status(
    place_id: list[str] = Query(default=[], max_length=100),
    controller: SavedHotelController = Depends(get_saved_hotel_controller),
) -> SavedHotelStatusResponse:
    return SavedHotelStatusResponse(saved_ids=controller.status(place_id))


@app.post("/api/saved-hotels", response_model=SaveHotelResponse)
def save_hotel(
    request: SaveHotelRequest,
    controller: SavedHotelController = Depends(get_saved_hotel_controller),
) -> SaveHotelResponse:
    return SaveHotelResponse(hotel=controller.save(request))


@app.delete("/api/saved-hotels", response_model=RemoveHotelResponse)
def remove_hotel(
    place_id: str = Query(min_length=1),
    controller: SavedHotelController = Depends(get_saved_hotel_controller),
) -> RemoveHotelResponse:
    controller.remove(place_id)
    return RemoveHotelResponse(place_id=place_id)


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
