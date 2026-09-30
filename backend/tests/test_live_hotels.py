"""Live hotel discovery tests; every provider response is mocked locally."""

from contextlib import contextmanager

import httpx
import pytest
from fastapi.testclient import TestClient

from backend import config
from backend.controllers.location import (
    InvalidZipError,
    LocationController,
    ProviderFailureError,
    UnresolvedZipError,
)
from backend.main import app, get_location_controller


TEST_KEY = "mock-provider-key"


def geocode_result(postcode="02108", **changes):
    result = {
        "postcode": postcode,
        "country_code": "us",
        "result_type": "postcode",
        "city": "Boston",
        "state": "Massachusetts",
        "lat": 42.36,
        "lon": -71.06,
    }
    result.update(changes)
    return result


def hotel_feature(name="Sample Hotel", **changes):
    properties = {
        "place_id": "provider-place-1",
        "name": name,
        "formatted": "1 Sample Street, Boston, MA",
    }
    properties.update(changes)
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-71.061, 42.361]},
        "properties": properties,
    }


@contextmanager
def mocked_provider(geocoding=None, places=None):
    requests = []
    geocoding = geocoding if geocoding is not None else {"results": [geocode_result()]}
    places = places if places is not None else {"features": [hotel_feature()]}

    def respond(request):
        requests.append(request)
        if request.url.path == "/v1/geocode/search":
            response = geocoding
        elif request.url.path == "/v2/places":
            response = places
        else:
            raise AssertionError("Unexpected provider path")
        if callable(response):
            return response(request)
        return httpx.Response(200, json=response)

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        yield client, requests


@contextmanager
def live_route(provider):
    app.dependency_overrides[get_location_controller] = lambda: LocationController(
        client=provider, api_key=TEST_KEY
    )
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def test_leading_zero_zip_and_successful_provider_mapping():
    with mocked_provider() as (provider, requests):
        result = LocationController(provider, TEST_KEY).search_live_hotels("02108")

    assert result.search_center.requested_zip == "02108"
    assert result.search_center.resolved_postcode == "02108"
    assert result.search_center.city == "Boston"
    assert result.hotels[0].place_id == "provider-place-1"
    assert result.hotels[0].name == "Sample Hotel"
    assert result.hotels[0].formatted_address == "1 Sample Street, Boston, MA"
    assert result.hotels[0].latitude == 42.361
    assert result.hotels[0].longitude == -71.061
    assert len(requests) == 2

    geocode, places = requests
    assert geocode.url.path == "/v1/geocode/search"
    assert dict(geocode.url.params) == {
        "text": "02108",
        "type": "postcode",
        "filter": "countrycode:us",
        "format": "json",
        "limit": "5",
        "apiKey": TEST_KEY,
    }
    assert places.url.path == "/v2/places"
    assert dict(places.url.params) == {
        "categories": "accommodation.hotel",
        "filter": "circle:-71.06,42.36,5000",
        "bias": "proximity:-71.06,42.36",
        "limit": "20",
        "apiKey": TEST_KEY,
    }


@pytest.mark.parametrize("zip_code", ["2108", "02A08", "02108-1234", " 02108", "٠٢١٠٨"])
def test_invalid_zip_never_calls_provider(zip_code):
    with mocked_provider() as (provider, requests):
        with pytest.raises(InvalidZipError):
            LocationController(provider, TEST_KEY).search_live_hotels(zip_code)
    assert requests == []


@pytest.mark.parametrize(
    "geocoding",
    [
        {"results": [geocode_result(postcode="02109")]},
        {"results": [geocode_result(country_code="ca")]},
        {"results": []},
    ],
)
def test_mismatched_or_missing_us_postcode_is_unresolved(geocoding):
    with mocked_provider(geocoding=geocoding) as (provider, requests):
        with pytest.raises(UnresolvedZipError):
            LocationController(provider, TEST_KEY).search_live_hotels("02108")
    assert len(requests) == 1


def test_valid_empty_places_result_is_success():
    with mocked_provider(places={"features": []}) as (provider, requests):
        result = LocationController(provider, TEST_KEY).search_live_hotels("02108")
    assert result.hotels == []
    assert len(requests) == 2


def test_missing_hotel_name_uses_honest_fallback_and_omits_missing_address():
    feature = hotel_feature(name="", formatted=None)
    with mocked_provider(places={"features": [feature]}) as (provider, _):
        with live_route(provider) as client:
            response = client.get("/api/live-hotels", params={"zip": "02108"})
    assert response.status_code == 200
    hotel = response.json()["hotels"][0]
    assert hotel["name"] == "Name unavailable"
    assert "formatted_address" not in hotel


def test_live_route_returns_small_provider_backed_response_without_key():
    with mocked_provider() as (provider, _):
        with live_route(provider) as client:
            response = client.get("/api/live-hotels", params={"zip": "02108"})
    assert response.status_code == 200
    assert response.json() == {
        "search_center": {
            "requested_zip": "02108",
            "resolved_postcode": "02108",
            "city": "Boston",
            "state": "Massachusetts",
            "latitude": 42.36,
            "longitude": -71.06,
        },
        "hotels": [
            {
                "place_id": "provider-place-1",
                "name": "Sample Hotel",
                "formatted_address": "1 Sample Street, Boston, MA",
                "latitude": 42.361,
                "longitude": -71.061,
            }
        ],
    }
    assert TEST_KEY not in response.text
    assert "api.geoapify.com" not in response.text


@pytest.mark.parametrize(
    ("zip_code", "geocoding", "status", "detail"),
    [
        ("1234", None, 422, "Enter exactly five digits for a U.S. ZIP code."),
        ("02A08", None, 422, "Enter exactly five digits for a U.S. ZIP code."),
        ("02108", {"results": [geocode_result(postcode="02109")]}, 404, "ZIP code could not be resolved."),
        ("02108", {"results": []}, 404, "ZIP code could not be resolved."),
    ],
)
def test_route_validation_and_unresolved_errors(zip_code, geocoding, status, detail):
    with mocked_provider(geocoding=geocoding) as (provider, requests):
        with live_route(provider) as client:
            response = client.get("/api/live-hotels", params={"zip": zip_code})
    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert len(requests) == (0 if status == 422 else 1)
    assert TEST_KEY not in response.text


def test_geoapify_rate_limit_maps_to_429():
    with mocked_provider(
        geocoding=lambda _: httpx.Response(429, json={"message": "rate limited"})
    ) as (provider, requests):
        with live_route(provider) as client:
            response = client.get("/api/live-hotels", params={"zip": "02108"})
    assert response.status_code == 429
    assert response.json() == {
        "detail": "Hotel searches are temporarily limited. Try again later."
    }
    assert len(requests) == 1
    assert TEST_KEY not in response.text


@pytest.mark.parametrize(
    "failure",
    [
        lambda request: httpx.Response(500, json={"error": "provider failed"}),
        lambda request: (_ for _ in ()).throw(httpx.ConnectTimeout("credential-bearing URL", request=request)),
    ],
)
def test_provider_failure_maps_to_safe_502(failure):
    with mocked_provider(geocoding=failure) as (provider, _):
        with live_route(provider) as client:
            response = client.get("/api/live-hotels", params={"zip": "02108"})
    assert response.status_code == 502
    assert response.json() == {
        "detail": "Hotel search service is unavailable. Try again later."
    }
    assert TEST_KEY not in response.text
    assert "credential-bearing" not in response.text


def test_malformed_provider_data_is_failure_not_empty_success():
    with mocked_provider(places={"wrong_field": []}) as (provider, _):
        with pytest.raises(ProviderFailureError):
            LocationController(provider, TEST_KEY).search_live_hotels("02108")


def test_unusable_nonempty_places_response_is_provider_failure():
    feature = hotel_feature(place_id=None)
    with mocked_provider(places={"features": [feature]}) as (provider, _):
        with live_route(provider) as client:
            response = client.get("/api/live-hotels", params={"zip": "02108"})
    assert response.status_code == 502
    assert response.json() == {
        "detail": "Hotel search service is unavailable. Try again later."
    }


def test_matching_postcode_without_valid_coordinates_is_provider_failure():
    geocoding = {"results": [geocode_result(lat=None)]}
    with mocked_provider(geocoding=geocoding) as (provider, requests):
        with pytest.raises(ProviderFailureError):
            LocationController(provider, TEST_KEY).search_live_hotels("02108")
    assert len(requests) == 1


def test_missing_configuration_returns_safe_503_without_provider_call():
    with mocked_provider() as (provider, requests):
        app.dependency_overrides[get_location_controller] = lambda: LocationController(
            client=provider, api_key=""
        )
        try:
            with TestClient(app) as client:
                response = client.get("/api/live-hotels", params={"zip": "02108"})
        finally:
            app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "Hotel search service is not configured."}
    assert requests == []


def test_backend_env_key_loading_without_using_a_real_key(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GEOAPIFY_API_KEY=mock-file-key\n", encoding="utf-8")
    monkeypatch.setattr(config, "BACKEND_ENV_PATH", env_file)
    monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)
    assert config.get_geoapify_api_key() == "mock-file-key"

    monkeypatch.setenv("GEOAPIFY_API_KEY", "mock-environment-key")
    assert config.get_geoapify_api_key() == "mock-environment-key"
