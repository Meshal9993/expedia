Continue on feature/assignment2-part1-live-hotels.

The existing backend suite is passing again.

Now implement only the Assignment 2 Part 1 backend live-hotel search.

Do not modify the Vue frontend yet.
Do not implement Leaflet yet.
Do not commit yet.

Follow the contracts in:
- docs/assignment2-part1-contracts.md
- AGENTS.md

CHECK

Inspect:
- backend/main.py
- backend/models/
- backend/controllers/
- backend/requirements.txt
- existing API models and error patterns
- existing tests

Confirm where the new live-search model/controller should fit without mixing it with the existing SQLite booking models.

TAKE ACTION

1. MODEL / DTO

Add backend models for live provider data.

Create appropriate DTOs for:

LiveHotel:
- place_id: string
- name: string or honest fallback when missing
- formatted_address: optional string
- latitude: float
- longitude: float

SearchCenter:
- requested_zip: string
- resolved_postcode: string
- city: optional string
- state: optional string
- latitude: float
- longitude: float

LiveHotelSearchResponse:
- search_center
- hotels

Keep these separate from the original SQLite Hotel entity because live
Geoapify hotels do not have the original nightly_rate_usd field.

2. CONTROLLER

Create a dedicated Geoapify/location controller.

Responsibilities:

ZIP validation:
- accept only exactly five ASCII digits
- keep ZIP as a string
- preserve leading zeros
- invalid ZIP must be handled before calling Geoapify

Geoapify key:
- read GEOAPIFY_API_KEY from backend/.env/environment
- never print or return the key
- if missing, return a clear configuration/service error

Forward Geocoding request:
Use the official Geoapify endpoint:

https://api.geoapify.com/v1/geocode/search

Use parameters equivalent to:
- text=<requested ZIP>
- type=postcode
- filter=countrycode:us
- format=json
- limit=<small reasonable limit>
- apiKey=<server-side key>

Do not silently accept a different ZIP.

A resolved result must confirm:
- country_code is us
- postcode matches the requested ZIP

If no matching U.S. postcode is established, treat it as unresolved ZIP.

Use the matched result's latitude and longitude as the search center.

Places request:
Use:

https://api.geoapify.com/v2/places

Parameters:
- categories=accommodation.hotel
- filter=circle:<lon>,<lat>,5000
- bias=proximity:<lon>,<lat>
- limit=20
- apiKey=<server-side key>

Do not claim the results are exhaustive.

3. PROVIDER RESPONSE MAPPING

Map only provider-backed fields.

For every hotel:
- preserve Geoapify place_id/provider identifier
- use provider name if available
- use formatted address if available
- use provider coordinates

Do not invent:
- price
- rating
- room availability
- booking status

If a hotel name is missing, use a neutral honest label such as:
"Name unavailable"

Do not fabricate a hotel name.

4. ERROR HANDLING

Keep these situations separate:

422:
- invalid ZIP format

404:
- valid five-digit ZIP could not be resolved to the requested U.S. postcode

200 with hotels=[]:
- postcode resolved successfully but no nearby hotels were returned

429:
- recognized Geoapify quota/rate-limit response

502:
- other Geoapify/provider request failure

Do not convert provider failures into empty results.

5. FASTAPI

Add a thin route:

GET /api/live-hotels?zip=16801

The route should:
- validate through the controller/model contract
- delegate provider logic to the controller
- return the documented response DTO
- contain no Geoapify request construction or business logic itself

6. ENVIRONMENT FILES

Do not create backend/.env with a real key.

If not already present, create:
backend/.env.example

Containing only:

GEOAPIFY_API_KEY=your_key_here

Confirm:
- backend/.env is ignored by Git
- no API key appears in committed files

7. TESTS

Add mocked backend tests.

Tests must NOT spend Geoapify API quota.

Cover at least:

- valid ZIP preserves leading zero, e.g. 02108
- invalid ZIP shorter than 5 digits
- invalid ZIP containing letters
- geocoding confirms requested U.S. postcode
- geocoding returns a different postcode -> unresolved
- geocoding has no matching result -> unresolved
- successful hotel results
- successful empty hotel result
- hotel with missing name uses honest fallback
- Geoapify 429 maps to our 429 response
- provider failure maps to 502
- API key is not exposed in responses
- existing Assignment 1 hotel search still works

VERIFY

Run:
- full backend pytest suite
- git diff --check

Do not make a live Geoapify request yet unless a real local API key already
exists. If no key exists, verification should use mocked responses only.

DOCUMENTATION

Update handoffs/current.md truthfully:
- backend live-hotel search status
- mocked verification completed
- live Geoapify verification still pending if no key exists
- frontend list/map still pending

Save this major instruction as the next ordered prompt in prompts/.

Do not commit.

At the end report:
- files changed
- endpoint created
- exact Geoapify request shapes
- tests run/results
- whether a local GEOAPIFY_API_KEY exists without printing it
- remaining work
- git status

Stop for my review.