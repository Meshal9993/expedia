# Assignment 2, Part 1: live hotel search contracts

**Status:** complete, matching the [final report](../report.md) and assessed implementation commit `85d0ac345a451267742c456a3d1ee70e524e3f72`. This feature discovers hotel *places* near a U.S. ZIP code. It does not create bookings or change the instructor CSV/SQLite models.

## MVC ownership and models

| Layer | Responsibility |
| --- | --- |
| Model (`backend/models/live_hotels.py`) | Define immutable provider-backed `SearchCenter`, `LiveHotel`, and `LiveHotelSearchResponse` DTOs, separate from the existing CSV `Hotel` and `HotelStay` entities. |
| Controller (`backend/controllers/`) | A public `LocationController.search_live_hotels(zip_code: str)` validates and resolves the ZIP, requests nearby hotel places, validates provider data, and returns a search center plus live hotel results. It does not query SQLite. |
| HTTP (`backend/main.py`) | A thin route calls the controller and maps its typed outcomes to the JSON/status codes below. Existing hotel-name and booking routes remain independent. |
| View (`frontend/src/`) | Vue owns the form, states, hotel list, Leaflet map, and shared selection. It calls only the FastAPI route, never Geoapify or Python directly. |

`SearchCenter` contains required string `requested_zip`, string `resolved_postcode`, finite `latitude` and `longitude`; `city` and `state` are optional and appear only when returned. `LiveHotel` contains required provider `place_id`, `name`, finite `latitude` and `longitude`; `formatted_address` is optional and appears only when returned. A missing provider name becomes the honest label `Name unavailable`; omit unusable place features that lack required identity or coordinates. Do not add nightly price, rating, room availability, booking confirmation, or a local `hotel_id`: Geoapify Places does not establish a bookable stay.

## Controller and provider requests

The controller accepts **exactly** five ASCII digits (`^[0-9]{5}$`) as a string, including leading zeros; whitespace, ZIP+4, and numeric conversion are invalid. It reads `GEOAPIFY_API_KEY` from the process environment or backend-owned local `backend/.env`, uses a five-second timeout, and never logs credentials or full credential-bearing request URLs.

1. **Forward Geocoding:** `GET https://api.geoapify.com/v1/geocode/search` with `text=<ZIP>`, `type=postcode`, `filter=countrycode:us`, `format=json`, `limit=5`, and server-side `apiKey`. Select only a result whose `postcode` exactly matches the requested string, `country_code` is `us`, `result_type` is `postcode` when supplied, and coordinates are valid. A valid response without such a result is *unresolved ZIP*, not provider failure. Use its point as the search center.
2. **Places:** `GET https://api.geoapify.com/v2/places` with `categories=accommodation.hotel`, `filter=circle:<lon>,<lat>,5000`, `bias=proximity:<lon>,<lat>`, `limit=20`, and server-side `apiKey`. The filter sets the 5,000-meter radius; bias orders results. A circle does not itself prove every returned place is inside U.S. borders, so do not claim a broader country restriction than the verified U.S. postcode center. A result limit and provider coverage mean this is **not** an exhaustive hotel inventory.
3. Convert valid provider features to `LiveHotel`. A valid empty Places response is success with `hotels: []`. Timeout, non-success provider response, or malformed provider data is provider failure. Treat a recognizable rate-limit or quota response separately. The backend uses approved, directly declared `httpx==0.28.1` in its project-local virtual environment.

## HTTP contract

`GET /api/live-hotels?zip=16801` accepts one ZIP string. The following `200 OK` example is **illustrative**, not a claim that these locations were returned by Geoapify. Optional fields are omitted if absent; a successful search with no places returns the same `search_center` and `"hotels": []`.

```json
{
  "search_center": {
    "requested_zip": "16801",
    "resolved_postcode": "16801",
    "city": "Example city",
    "state": "PA",
    "latitude": 40.8,
    "longitude": -77.8
  },
  "hotels": [
    {
      "place_id": "provider-place-id",
      "name": "Provider hotel name",
      "formatted_address": "Address returned by provider",
      "latitude": 40.8,
      "longitude": -77.8
    }
  ]
}
```

The route passes even a missing `zip` value to controller validation so the invalid-input response is consistent. Error bodies follow the existing API's string `detail` convention; messages are fixed, safe text rather than raw provider errors.

| Condition | Status | Exact JSON body |
| --- | ---: | --- |
| Missing or invalid ZIP | 422 | `{"detail":"Enter exactly five digits for a U.S. ZIP code."}` |
| ZIP not resolved to matching U.S. postcode | 404 | `{"detail":"ZIP code could not be resolved."}` |
| Provider timeout, bad response, or service failure | 502 | `{"detail":"Hotel search service is unavailable. Try again later."}` |
| Recognized quota or rate limit | 429 | `{"detail":"Hotel searches are temporarily limited. Try again later."}` |
| Backend key missing | 503 | `{"detail":"Hotel search service is not configured."}` |

No response contains the API key, provider request URL, or raw exception text.

## Vue state contract

The single input is a ZIP string. Vue distinguishes `idle`, `loading`, `invalid ZIP`, `unresolved ZIP`, `results`, `no nearby hotels`, `provider/service failure`, and `quota/rate-limit failure`. Invalid input makes no API call. A `200` response with a nonempty `hotels` list shows the list and Leaflet markers; a `200` response with `hotels: []` shows “No nearby hotels were found within 5 km of this ZIP location.” The error status codes above select the other states. Clear or hide stale results when a new search starts or fails.

Vue holds one shared `selectedHotelId` equal to the selected result's `place_id`. Selecting a list item highlights its marker; selecting a marker highlights its list item. Map and data-source attribution remain visible. Neither the backend Geoapify key nor a provider request is placed in Vue code. `.gitignore` already ignores `.env` at the repository root and in `backend/`; never track `backend/.env`.

## Implemented request trace and verification

`frontend/src/App.vue` supplies the API base URL to `frontend/src/components/LiveHotelSearch.vue`. That component validates the ZIP string and requests `/api/live-hotels`; `backend/main.py` calls `LocationController.search_live_hotels` in `backend/controllers/location.py`. The controller reads the server-side key through `backend/config.py`, calls Geoapify geocoding and then Places, and returns the DTOs from `backend/models/live_hotels.py`. Vue passes the returned center, hotels, and shared selection to `frontend/src/components/HotelMap.vue`; OpenStreetMap supplies the tiles separately.

The final styling revision did not change this contract or Leaflet behavior. The [evidence log](assignment2-part1-evidence.md) records live `16801` and `02108`, invalid `1234`, synchronized selection, and mocked failure checks. Frontend lint/build and all 40 backend tests passed in the recorded final verification.
