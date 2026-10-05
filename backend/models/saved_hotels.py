"""Local hotel and classroom-night DTOs, separate from the frozen live API."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.models.live_hotels import SearchCenter


class SavedSearchCenter(SearchCenter):
    model_config = ConfigDict(frozen=True, extra="forbid")

    requested_zip: str = Field(strict=True, pattern=r"^[0-9]{5}$")
    resolved_postcode: str = Field(strict=True, pattern=r"^[0-9]{5}$")
    latitude: float = Field(strict=True, ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(strict=True, ge=-180, le=180, allow_inf_nan=False)

    @model_validator(mode="after")
    def matching_postcode(self):
        if self.requested_zip != self.resolved_postcode:
            raise ValueError("Resolved postcode must match the requested ZIP")
        return self


class SavedHotel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    place_id: str = Field(strict=True, min_length=1)
    name: str | None = None
    formatted_address: str | None = None
    latitude: float = Field(strict=True, ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(strict=True, ge=-180, le=180, allow_inf_nan=False)


class DemoHotelNight(BaseModel):
    model_config = ConfigDict(frozen=True)

    stay_date: date
    nightly_rate_cents: int = Field(ge=0)
    rooms_available: int = Field(ge=0)


class SavedHotelWithNights(SavedHotel):
    demo_nights: list[DemoHotelNight]


class SaveHotelRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    hotel: SavedHotel
    search_center: SavedSearchCenter


class SavedHotelSearchResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    search_center: SearchCenter | None
    hotels: list[SavedHotelWithNights]


class SaveHotelResponse(BaseModel):
    saved: bool = True
    hotel: SavedHotelWithNights


class SavedHotelStatusResponse(BaseModel):
    saved_ids: list[str]


class RemoveHotelResponse(BaseModel):
    place_id: str
    removed: bool = True
