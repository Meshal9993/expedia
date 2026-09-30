# Assignment 2, Part 1: live hotel search research

These decisions are implemented and verified as of September 30, 2026. A live place result identifies a hotel location; it does **not** prove that a room is available to book. See the [evidence log](assignment2-part1-evidence.md) for observed results and limitations.

## Interaction and layout

- Let the user enter a U.S. ZIP code and press **Search**. Keep the ZIP as text so a leading zero survives.
- Show hotel names and available addresses in a list beside a map on wide screens, with a stacked layout on narrow screens. Selecting a list row highlights its marker; selecting a marker highlights its row. Leaflet supports clickable markers and a visible attribution control ([reference](https://leafletjs.com/reference.html)).
- Show explicit loading, empty, and error feedback near the results rather than leaving an old map or list looking current.

## API decisions

1. Accept exactly five ASCII digits (`^[0-9]{5}$`) in both the View and the FastAPI boundary. Do not convert the ZIP to a number.
2. The backend geocodes it with Geoapify Forward Geocoding using `text=<ZIP>`, `type=postcode`, `filter=countrycode:us`, and `format=json`. Accept a center only when the response matches the requested postcode and U.S. country code and has valid coordinates. The country filter matters because postcodes are not globally unique ([Forward Geocoding](https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/)).
3. The backend searches Geoapify Places with `categories=accommodation.hotel` and `filter=circle:lon,lat,5000`, centered on that geocoded point. A proximity bias can order nearby results; the circle filter enforces the 5 km radius. Places returns point locations and may include names and addresses ([Places API](https://apidocs.geoapify.com/docs/places/)). A result limit means the list may not be a complete inventory.
4. Return only supported place details to Vue, such as name, address if present, coordinates, and a stable place identifier. Do not invent price, rating, room availability, or booking data. Keep these live places separate from the supplied SQLite hotels and their booking records.

## Implemented states

| State | Message or behavior |
| --- | --- |
| Loading | Show “Searching nearby hotels…” and prevent duplicate submissions. |
| Invalid ZIP | Ask for exactly five digits before calling the backend. |
| Unresolved ZIP | Explain that the ZIP could not be found. |
| No nearby hotels | Say “No hotels found within 5 km” after a successful search. |
| API/service failure | Say the service is unavailable and offer a retry. |
| Quota/rate-limit failure | Explain that searches are temporarily limited and suggest trying later. |

## Security, usage, and Booking decisions

- Keep the backend Geoapify key in a local `backend/.env`; `.env` is currently ignored and untracked. Vue sends the ZIP to FastAPI and never receives the key. The backend owns provider calls and returns a small JSON response, following the project's MVC boundaries.
- The implementation uses public OpenStreetMap tiles. Leaflet and OpenStreetMap attribution remain visible on the map; a Geoapify data credit appears below it. The tile layer contains no Geoapify key ([Leaflet reference](https://leafletjs.com/reference.html)).
- Each successful lookup makes one backend geocoding call followed by one Places call. Current credit allowances and rate limits depend on the provider plan; consult the account and [Geoapify pricing](https://www.geoapify.com/pricing/) rather than treating earlier planning figures as a guarantee. Validate before provider calls, use finite timeouts, and handle quota or rate errors separately.
- Preserve the existing hotel-name search and demo booking flow. Live ZIP search has its own discovery view and remains separate from booking records.
- Use a simple student-project presentation: light background, basic bordered rows, modest headings, and clear selected/focus states. The final styling revision preserves the desktop side-by-side and narrow-screen stacked layout.
