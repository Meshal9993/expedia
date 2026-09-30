Continue on feature/assignment2-part1-live-hotels.

The Assignment 2 live-hotel backend is implemented and live-verified.

Now implement the Vue View and Leaflet map for Assignment 2 Part 1.

Do not commit yet.
Do not expose GEOAPIFY_API_KEY in frontend code.
Do not modify backend/.env.
Do not invent hotel prices, ratings, availability, or booking information.

Preserve the existing Assignment 1 behavior unless a change is required for the new interface.

FOLLOW MVC

View:
- Vue components
- search form
- hotel list
- Leaflet map
- loading/error/result states
- shared hotel selection
- CSS

Controller/backend:
- live ZIP/hotel provider logic stays in the backend
- frontend only calls GET /api/live-hotels?zip=...

Do not move provider logic into Vue.

CHECK

First inspect:
- frontend/src/App.vue
- frontend/src/styles.css
- frontend/package.json
- current frontend structure
- docs/assignment2-part1-mockup.md
- docs/assignment2-part1-contracts.md
- AGENTS.md

Confirm Leaflet 1.9.4 is installed.

TAKE ACTION

1. ADD A LIVE HOTEL SEARCH SECTION

Add a clearly labeled section such as:

Live Hotel Search

Include:
- one ZIP code input
- Search button

The ZIP input must:
- be treated as text, not a number
- preserve leading zeros
- accept a five-digit U.S. ZIP code
- not silently change the entered ZIP

Do not make the browser input type="number".

2. SEARCH BEHAVIOR

When the user submits:

GET /api/live-hotels?zip=<ZIP>

Use the backend response only.

Handle these states separately:

Idle:
- show basic instructions

Loading:
- show a clear message such as:
  "Searching for hotels..."

Invalid ZIP:
- display a useful validation message

Unresolved ZIP:
- explain that the ZIP could not be resolved

Successful results:
- show the returned hotels

Successful search with no hotels:
- clearly say that no nearby hotels were found within 5 km

Provider/service failure:
- show a service error
- do not describe it as "no hotels found"

Rate/quota error:
- show a separate temporary service-limit message when the backend returns 429

3. RESULTS SUMMARY

After a successful search, show a small summary such as:

Hotels near 16801
State College, Pennsylvania

Use only search_center information returned by the backend.

Do not claim the results are all hotels in the ZIP code.
A suitable sentence is:

"Hotels returned by the provider within 5 km of the resolved ZIP location."

4. HOTEL LIST

Display every returned hotel in a readable list/card.

Show only provider-backed fields:

- hotel name
- address when available

If the backend returns "Name unavailable", display it honestly.

Do not add:
- price
- rating
- rooms
- availability
- booking buttons
- fake descriptions

Each hotel item must be selectable.

Use place_id as the provider identity.

5. LEAFLET MAP

Use the installed Leaflet package.

Import Leaflet and its CSS through the Vue/frontend project.

Create a map centered on:

search_center.latitude
search_center.longitude

Display one marker for each hotel using its returned coordinates.

Use a normal public tile layer appropriate for this coursework.

Keep the required tile/map attribution visibly enabled.

Do not hide attribution with CSS.

Do not use GEOAPIFY_API_KEY in the frontend tile configuration.

6. SYNCHRONIZED SELECTION

Maintain one shared selected hotel identity, for example:

selectedHotelId

List -> Map:
- clicking/selecting a hotel in the list selects the matching marker
- visually highlight the selected list item
- move/focus/open the matching marker popup when useful

Map -> List:
- clicking a marker selects the matching hotel in the list
- visually highlight the same list item
- scroll the selected list item into view if practical

Both representations must always refer to the same place_id.

Do not create separate unrelated selection state for list and map.

7. MAP LIFECYCLE

Handle Leaflet correctly with Vue:

- create the map after the map DOM element exists
- avoid creating duplicate map instances
- clear or replace old markers after a new search
- recenter the map for the new search center
- clean up the Leaflet map when the component is unmounted

If results are empty, do not leave misleading markers from the previous search.

8. KEYBOARD / ACCESSIBILITY

Make search and list controls usable with the keyboard.

- Search button should be keyboard accessible
- selectable hotel results should be keyboard accessible
- provide visible focus styles
- do not rely only on marker color to communicate selection
- associate the ZIP label with its input

9. RESPONSIVE LAYOUT

Follow the early mockup:

Desktop:
- hotel list and map side by side when space allows

Narrow/mobile:
- stack list and map vertically

Keep the design simple and readable.

Do not copy Expedia exactly.

10. PRESERVE OLD FUNCTIONALITY

Do not remove working Assignment 1 functionality.

Keep the old local booking/SQLite application separate from the new live Geoapify results.

Live Geoapify hotels must NOT automatically become SQLite booking hotels.

11. VERIFICATION

Run:

- npm run lint
- npm run build
- full backend pytest suite
- git diff --check

Then start backend and frontend.

Use the browser to verify:

A. Search:
16801

Expected:
- successful search
- State College search center
- live hotels in list
- map centered correctly
- markers displayed

B. Click one hotel in the list.
Expected:
- same hotel selected on map

C. Click a different map marker.
Expected:
- same hotel becomes selected in list

D. Search:
02108

Expected:
- leading zero preserved
- Boston search center
- old State College markers removed/replaced
- new results shown

E. Search:
1234

Expected:
- invalid ZIP state
- no misleading previous results

F. Use a mocked/safe failure path if available to verify:
- unresolved ZIP
- empty results
- provider failure
- 429/rate-limit state

Do not intentionally exhaust the live API quota.

12. DOCUMENTATION

Save this major instruction as the next ordered prompt in prompts/.

Update handoffs/current.md with:
- Vue live ZIP search status
- Leaflet map status
- synchronized list/map selection status
- live ZIPs tested
- remaining manual verification/evidence work

Do not write report.md yet.
Do not commit yet.

At the end report:

- frontend files changed
- UI behavior implemented
- Leaflet implementation details
- tile provider and attribution used
- live searches tested
- list/map synchronization result
- error states tested
- frontend lint/build results
- backend test results
- any remaining issues
- git status

Stop for my review.