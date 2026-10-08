# Part 2 RAG context example

This is deterministic **fixture/mocked evidence**, not live OpenAI or Geoapify evidence. [Fictional fixture data](assignment2-part2-rag-fixture.json) is loaded only into temporary test databases. Real course records were not replaced.

Question: “Find fixture-alpha in ZIP 02108 for 2026-10-10 to 2026-10-13, two rooms.”

Schema: `saved_hotels(hotel_id,name,address,latitude,longitude)`; `saved_hotel_locations(hotel_id,requested_zip,resolved_postcode,city,state,latitude,longitude)`; `demo_hotel_nights(hotel_id,stay_date,nightly_rate_cents,rooms_available)`.

The first mocked Responses request proposes:

```sql
SELECT h.hotel_id, h.name, l.requested_zip,
       n.stay_date, n.nightly_rate_cents, n.rooms_available
FROM saved_hotels h
JOIN saved_hotel_locations l ON h.hotel_id = l.hotel_id
LEFT JOIN demo_hotel_nights n ON h.hotel_id = n.hotel_id
  AND n.stay_date >= ? AND n.stay_date < ?
WHERE l.requested_zip = ? AND h.hotel_id = ?
ORDER BY n.stay_date
```

Parameters: `["2026-10-10","2026-10-13","02108","fixture-alpha"]`. Stay: `{check_in:"2026-10-10",check_out:"2026-10-13",rooms:2}`. Both joins preserve the same hotel identity. Executed SQL wraps the proposal as `SELECT * FROM (<validated query>) AS rag_rows LIMIT 51`; at most 50 rows are returned and exact executed SQL is saved.

Retrieved rows all identify `fixture-alpha`, Fixture Alpha Hotel, ZIP **"02108"**:

| Date | Demo rate (cents) | Simulated rooms |
| --- | ---: | ---: |
| 2026-10-10 | 10000 | 20 |
| 2026-10-11 | 12000 | 3 |
| 2026-10-12 | 9000 | 5 |

October 13 is excluded checkout, even though the fixture contains that date. All three required nights exist, with at least two simulated rooms nightly. Per-room total: **31000 cents ($310.00)**.

The second mocked request receives the original question, these exact rows, query context, and backend coverage checks. Final checked stay answer:

> Fixture Alpha Hotel (fixture-alpha): 3 nights; per-room demo total $310.00. At least 2 simulated room(s) exist on each required night.
>
> Rates and room availability are simulated classroom data, not live hotel information.

The missing-night hotel has no October 11 row: full-stay total/availability remain unknown. ZIP `99999` gives empty success. Provider failure and rejected SQL have separate errors.

Tests create temporary conversation UUIDs, persist stages, reopen SQLite, and load history through the endpoint. **Live conversation ID: pending; no live model request performed.** Add a real ID and observed live wording only after later live verification.
