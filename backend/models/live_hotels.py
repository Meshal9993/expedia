"""Provider-backed location data, separate from the SQLite booking entities."""

from pydantic import BaseModel, ConfigDict, Field


class SearchCenter(BaseModel):
    model_config = ConfigDict(frozen=True)

    requested_zip: str
    resolved_postcode: str
    city: str | None = None
    state: str | None = None
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class LiveHotel(BaseModel):
    model_config = ConfigDict(frozen=True)

    place_id: str
    name: str
    formatted_address: str | None = None
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class LiveHotelSearchResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    search_center: SearchCenter
    hotels: list[LiveHotel]
