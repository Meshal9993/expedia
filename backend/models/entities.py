"""Entities represented by the instructor CSVs and the local database."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Hotel:
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: float


@dataclass(frozen=True)
class Trip:
    trip_id: str
    hotel_id: str
    trip_name: str
    check_in: str
    check_out: str


@dataclass(frozen=True)
class User:
    user_id: str
    display_name: str


@dataclass(frozen=True)
class Booking:
    booking_id: str
    user_id: str
    trip_id: str
    booked_on: str
    status: str


@dataclass(frozen=True)
class HotelStay:
    hotel_id: str
    hotel_name: str
    city: str
    state: str
    nightly_rate_usd: float
    trip_id: str
    trip_name: str
    check_in: str
    check_out: str
