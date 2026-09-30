"""Geoapify postcode resolution and nearby hotel-place discovery."""

import math
import re

import httpx

from backend.config import get_geoapify_api_key
from backend.models.live_hotels import LiveHotel, LiveHotelSearchResponse, SearchCenter


GEOCODING_URL = "https://api.geoapify.com/v1/geocode/search"
PLACES_URL = "https://api.geoapify.com/v2/places"
REQUEST_TIMEOUT_SECONDS = 5.0
ZIP_PATTERN = re.compile(r"[0-9]{5}")


class LocationError(Exception):
    """Base class for safe, typed live-search failures."""


class InvalidZipError(LocationError):
    """The submitted value is not exactly five ASCII digits."""


class UnresolvedZipError(LocationError):
    """No matching U.S. postcode location was found."""


class LocationConfigurationError(LocationError):
    """The backend Geoapify key is missing."""


class ProviderRateLimitError(LocationError):
    """Geoapify identified a quota or rate-limit condition."""


class ProviderFailureError(LocationError):
    """Geoapify did not return a usable response."""


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _coordinates(latitude: object, longitude: object) -> tuple[float, float] | None:
    if isinstance(latitude, bool) or isinstance(longitude, bool):
        return None
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return None
    if not (math.isfinite(latitude) and math.isfinite(longitude)):
        return None
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None
    return float(latitude), float(longitude)


def _feature_coordinates(feature: dict, properties: dict) -> tuple[float, float] | None:
    geometry = feature.get("geometry")
    if isinstance(geometry, dict) and geometry.get("type") == "Point":
        values = geometry.get("coordinates")
        if isinstance(values, list) and len(values) >= 2:
            point = _coordinates(values[1], values[0])
            if point is not None:
                return point
    return _coordinates(properties.get("lat"), properties.get("lon"))


class LocationController:
    """Search live hotel places without touching the local booking database."""

    def __init__(
        self,
        client: httpx.Client | None = None,
        api_key: str | None = None,
    ) -> None:
        self.client = client
        self.api_key = api_key

    def search_live_hotels(self, zip_code: str) -> LiveHotelSearchResponse:
        if not isinstance(zip_code, str) or ZIP_PATTERN.fullmatch(zip_code) is None:
            raise InvalidZipError

        key = self.api_key if self.api_key is not None else get_geoapify_api_key()
        if not key or not key.strip():
            raise LocationConfigurationError

        if self.client is None:
            with httpx.Client() as client:
                return self._search(client, zip_code, key.strip())
        return self._search(self.client, zip_code, key.strip())

    def _search(self, client: httpx.Client, zip_code: str, key: str) -> LiveHotelSearchResponse:
        geocoding = self._request_json(
            client,
            GEOCODING_URL,
            {
                "text": zip_code,
                "type": "postcode",
                "filter": "countrycode:us",
                "format": "json",
                "limit": 5,
                "apiKey": key,
            },
        )
        center = self._search_center(geocoding, zip_code)
        longitude, latitude = center.longitude, center.latitude
        places = self._request_json(
            client,
            PLACES_URL,
            {
                "categories": "accommodation.hotel",
                "filter": f"circle:{longitude},{latitude},5000",
                "bias": f"proximity:{longitude},{latitude}",
                "limit": 20,
                "apiKey": key,
            },
        )
        return LiveHotelSearchResponse(
            search_center=center,
            hotels=self._hotel_results(places),
        )

    @staticmethod
    def _request_json(client: httpx.Client, url: str, params: dict) -> dict:
        try:
            response = client.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        except httpx.RequestError:
            raise ProviderFailureError from None

        if response.status_code == 429 or (
            response.status_code in (402, 403)
            and any(term in response.text.lower() for term in ("quota", "rate limit", "rate-limit"))
        ):
            raise ProviderRateLimitError
        if response.status_code != 200:
            raise ProviderFailureError
        try:
            data = response.json()
        except ValueError:
            raise ProviderFailureError from None
        if not isinstance(data, dict):
            raise ProviderFailureError
        return data

    @staticmethod
    def _search_center(data: dict, zip_code: str) -> SearchCenter:
        results = data.get("results")
        if not isinstance(results, list) or any(not isinstance(item, dict) for item in results):
            raise ProviderFailureError

        matched_without_coordinates = False
        for item in results:
            if (
                item.get("postcode") != zip_code
                or str(item.get("country_code", "")).lower() != "us"
                or item.get("result_type", "postcode") != "postcode"
            ):
                continue
            point = _coordinates(item.get("lat"), item.get("lon"))
            if point is None:
                matched_without_coordinates = True
                continue
            return SearchCenter(
                requested_zip=zip_code,
                resolved_postcode=item["postcode"],
                city=_text(item.get("city")),
                state=_text(item.get("state")),
                latitude=point[0],
                longitude=point[1],
            )

        if matched_without_coordinates:
            raise ProviderFailureError
        raise UnresolvedZipError

    @staticmethod
    def _hotel_results(data: dict) -> list[LiveHotel]:
        features = data.get("features")
        if not isinstance(features, list):
            raise ProviderFailureError

        hotels = []
        seen_ids = set()
        for feature in features:
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                continue
            place_id = _text(properties.get("place_id")) or _text(feature.get("id"))
            point = _feature_coordinates(feature, properties)
            if place_id is None or point is None or place_id in seen_ids:
                continue
            seen_ids.add(place_id)
            hotels.append(
                LiveHotel(
                    place_id=place_id,
                    name=_text(properties.get("name")) or "Name unavailable",
                    formatted_address=_text(properties.get("formatted"))
                    or _text(properties.get("formatted_address")),
                    latitude=point[0],
                    longitude=point[1],
                )
            )
        if features and not hotels:
            raise ProviderFailureError
        return hotels
