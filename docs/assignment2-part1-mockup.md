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

The list and map share one selection: choosing a hotel row highlights its marker, and choosing a marker highlights its row. On a narrow screen, the list and map can stack. This mockup may change during implementation.

Planned feedback in the results area:

```text
Loading...                         Searching nearby hotels...
Invalid ZIP code                   Enter exactly five digits.
ZIP code could not be found        Check the ZIP and try again.
No hotels found within 5 km        Try another ZIP code.
Service unavailable               Please retry later.
Searches temporarily limited      Please try again later.
```

No price, rating, or availability will be shown unless the API actually provides it. A place on the map is not a bookable stay.

## Final outcome — September 30, 2026

The early sketch is retained as planning evidence. The implemented heading is **Live Hotel Search**, and the input accepts any five-digit U.S. ZIP string. The list/map arrangement, shared selection, and feedback states were retained. Styling was simplified to a light background, modest headings, basic buttons, and bordered hotel rows; the decorative eyebrow and list number badges were removed. Map markers and attribution remain. No live price, rating, availability, or booking fields were added. See the [demo video and verification](assignment2-part1-evidence.md).
