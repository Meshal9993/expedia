"""Booking business rules built on the database CRUD contract."""

from dataclasses import asdict, replace
from datetime import date

from backend.controllers.database import DatabaseController
from backend.models.entities import Booking, Hotel, Trip, User


class BookingNotFoundError(LookupError):
    """Raised when a requested booking does not exist."""


class BookingReferenceError(ValueError):
    """Raised when a booking references an unknown user or trip."""


class BookingController:
    """Create, retrieve, cancel, and delete bookings through persistence CRUD."""

    def __init__(self, database: DatabaseController):
        self.database = database

    def create_booking(
        self,
        user_id: str,
        trip_id: str,
        booked_on: date,
    ) -> dict[str, dict]:
        user_id = user_id.strip()
        trip_id = trip_id.strip()
        self._get_reference(User, user_id, "Traveler")
        self._get_reference(Trip, trip_id, "Trip")

        booking = Booking(
            booking_id=self._next_booking_id(),
            user_id=user_id,
            trip_id=trip_id,
            booked_on=booked_on.isoformat(),
            status="confirmed",
        )
        self.database.create(booking)
        return self._details(booking)

    def get_history(self, user_id: str | None = None) -> list[dict[str, dict]]:
        normalized_user_id = user_id.strip() if user_id is not None else None
        if normalized_user_id is not None:
            self._get_reference(User, normalized_user_id, "Traveler")

        bookings = self.database.list(Booking)
        if normalized_user_id is not None:
            bookings = [
                booking
                for booking in bookings
                if booking.user_id == normalized_user_id
            ]
        return [self._details(booking) for booking in bookings]

    def get_booking(self, booking_id: str) -> dict[str, dict]:
        return self._details(self._get_booking(booking_id))

    def cancel_booking(self, booking_id: str) -> dict[str, dict]:
        booking = self._get_booking(booking_id)
        cancelled = replace(booking, status="cancelled")
        self.database.update(cancelled)
        return self._details(cancelled)

    def delete_booking(self, booking_id: str) -> dict[str, str | bool]:
        normalized_id = booking_id.strip()
        try:
            self.database.delete(Booking, normalized_id)
        except KeyError as error:
            raise BookingNotFoundError(
                f"Booking {normalized_id!r} was not found"
            ) from error
        return {"booking_id": normalized_id, "deleted": True}

    def _next_booking_id(self) -> str:
        booking_ids = {booking.booking_id for booking in self.database.list(Booking)}
        numbers = [
            int(booking_id[1:])
            for booking_id in booking_ids
            if booking_id.startswith("B") and booking_id[1:].isdigit()
        ]
        next_number = max(numbers, default=0) + 1
        while True:
            candidate = f"B{next_number:03d}"
            if candidate not in booking_ids:
                return candidate
            next_number += 1

    def _get_booking(self, booking_id: str) -> Booking:
        normalized_id = booking_id.strip()
        try:
            return self.database.get(Booking, normalized_id)
        except KeyError as error:
            raise BookingNotFoundError(
                f"Booking {normalized_id!r} was not found"
            ) from error

    def _get_reference(self, model: type[User] | type[Trip], record_id: str, label: str):
        try:
            return self.database.get(model, record_id)
        except KeyError as error:
            raise BookingReferenceError(
                f"{label} {record_id!r} was not found"
            ) from error

    def _details(self, booking: Booking) -> dict[str, dict]:
        user = self.database.get(User, booking.user_id)
        trip = self.database.get(Trip, booking.trip_id)
        hotel = self.database.get(Hotel, trip.hotel_id)
        return {
            "booking": asdict(booking),
            "traveler": asdict(user),
            "trip": asdict(trip),
            "hotel": asdict(hotel),
        }
