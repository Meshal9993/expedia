"""HTTP request models for the FastAPI boundary."""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class BookingCreateRequest(BaseModel):
    user_id: str
    trip_id: str
    booked_on: date


class BookingUpdateRequest(BaseModel):
    status: Literal["cancelled"]
