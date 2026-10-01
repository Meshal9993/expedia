# Assignment 2, Part 1: early layout mockup

```text
------------------------------------------------------------
Booking
Find hotels near a U.S. ZIP code

[ ZIP Code: 16802      ] [ Search ]
------------------------------------------------------------
Results near 16802 (within 5 km)

Hotel list                           Map
-------------------------------      -----------------------
Hotel Name 1                         |       pin 1         |
Address, if provided                 |                     |
[ selected ]                          |  pin 2              |
                                     |                     |
Hotel Name 2                         |  map attribution    |
Address, if provided                 -----------------------
------------------------------------------------------------
```

This is the original planning sketch; `16802` was an early example, not a final verification ZIP. The list and map share one selection: choosing a hotel row highlights its marker, and choosing a marker highlights its row. On a narrow screen, the list and map stack. The sketch was allowed to change during implementation.

Planned feedback in the results area:

```text
Loading...                         Searching nearby hotels...
Invalid ZIP code                   Enter exactly five digits.
ZIP code could not be found        Check the ZIP and try again.
No hotels found within 5 km        Try another ZIP code.
Service unavailable               Please retry later.
Searches temporarily limited      Please try again later.
```

The final UI shows no price, rating, availability, or booking information. A place on the map is not a bookable stay.

## Final outcome — September 30, 2026

The implemented heading is **Live Hotel Search**, with an empty text ZIP input (placeholder `e.g. 16801`), a **Search** button, and an idle instruction. Results show `Hotels near <ZIP>`, a **Hotel places** list, and a **Map · within 5 km**. The layout and shared selection follow the sketch; loading, invalid, unresolved, empty, service-failure, and rate-limit messages remain.

The final style uses a light background, modest headings, basic buttons, bordered rows, and clear selected/focus states. Map attribution stays visible. The [report](../report.md) and [evidence log](assignment2-part1-evidence.md) record final checks with `16801`, `02108`, and invalid `1234`.
