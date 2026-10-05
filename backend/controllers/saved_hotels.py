"""Local-save business rules; persistence stays in DatabaseController."""

import re
import sqlite3
from datetime import date

from backend.controllers.database import DatabaseController
from backend.controllers.location import InvalidZipError
from backend.models.saved_hotels import SaveHotelRequest


DEMO_STAY_DATES = tuple(date(2026, 10, day) for day in range(10, 15))


class LocalStorageError(Exception):
    """Local storage failed; raw database errors must stay out of responses."""


class SavedHotelNotFoundError(Exception):
    """The requested provider ID is not saved."""


class SavedHotelController:
    def __init__(self, database: DatabaseController):
        self.database = database

    @staticmethod
    def _storage(operation, *args):
        try:
            return operation(*args)
        except sqlite3.Error:
            raise LocalStorageError from None

    def save(self, request: SaveHotelRequest):
        hotel = request.hotel
        # Part 1's fixed display fallback is not an API-supplied hotel name.
        if hotel.name == "Name unavailable" or not (hotel.name or "").strip():
            hotel = hotel.model_copy(update={"name": None})
        return self._storage(
            self.database.save_api_hotel, hotel, request.search_center, DEMO_STAY_DATES,
        )

    def search(self, zip_code: str):
        if re.fullmatch(r"[0-9]{5}", zip_code) is None:
            raise InvalidZipError
        return self._storage(self.database.get_saved_hotels, zip_code)

    def status(self, place_ids: list[str]):
        return self._storage(self.database.saved_hotel_ids, place_ids)

    def remove(self, place_id: str) -> None:
        try:
            self._storage(self.database.delete_saved_hotel, place_id)
        except KeyError:
            raise SavedHotelNotFoundError from None
