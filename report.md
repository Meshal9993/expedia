# Booking — Assignment 2 Part 1

## Project access

Repository:
https://github.com/Meshal9993/expedia

commit:
85d0ac345a451267742c456a3d1ee70e524e3f72

Frontend:
http://127.0.0.1:5173

Backend:
http://127.0.0.1:8000

The Geoapify API key is stored in backend/.env.


## Research notes

Before starting the implementation, I checked the Geoapify and Leaflet documentation.

Sources:

- https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/
- https://apidocs.geoapify.com/docs/places/
- https://leafletjs.com/reference.html
- https://www.geoapify.com/pricing/


The API key is kept in the backend and is not exposed in the frontend.

The application only displays information returned by Geoapify. 


## Early mockup

Before coding, I created a simple mockup showing the main parts of the page:

- ZIP code input
- Search button
- hotel list
- map
- different messages for loading and errors

Mockup:
https://github.com/Meshal9993/expedia/blob/main/docs/assignment2-part1-mockup.md


## Implementation

The user enters a five digit U.S. ZIP code.

The backend uses Geoapify to find the ZIP code location and search for nearby hotels within 5 km.

The frontend displays the results in a hotel list and a Leaflet map.

Selecting a hotel from the list selects the same hotel on the map. Selecting a marker on the map also selects the hotel in the list.

The application handles invalid ZIP codes, missing locations, no results, API errors, and rate limits.


## Demo video

Video:
https://github.com/Meshal9993/expedia/blob/main/docs/screenshots/Screen%20Recording%202026-09-30%20at%207.14.18%E2%80%AFPM.mov


## Verification

I tested the application:

For ZIP code 16801, the search returned State College and 15 hotel results during my test.

For ZIP code 02108, the leading zero was preserved and the search returned Boston with 20 results during my test.

I also tested:

- list to map selection
- map to list selection
- invalid ZIP (1234)
- no results
- API failure
- rate limit

All tests passed.

The original hotel search from Assignment 1 still works.


## AI disclosure and evidence log

I used Codex for coding, testing, and reviewing the project.

I also used the Codex Annotate/comment feature to select specific parts of the interface and give feedback.

The full evidence log is available here:

https://github.com/Meshal9993/expedia/blob/main/docs/assignment2-part1-evidence.md