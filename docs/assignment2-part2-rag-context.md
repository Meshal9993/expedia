# Part 2 RAG verification and context

## LIVE MODEL CHECK — October 8, 2026

Implementation checkpoint: `c143b4464709138f052d00b704e66b0c2ed76334`, branch `rag_integration`. Frontend: `http://127.0.0.1:5173/`; backend: `http://127.0.0.1:8000`. Both were restarted using the project runtime. Provider/model remained OpenAI / `gpt-5.6-luna`; keys stayed server-side.

### Actual saved data and question choice

Before any model request, SQLite contained one saved Courtyard by Marriott State College hotel, one ZIP association for **16801**, and five demo nights (October 10–14, 2026). No saved association used 16803, so the class example was adapted to 16801. October 11 had **10000 cents ($100.00)** and **5 simulated rooms**. The ZIP list/map and chatbot loaded; no credential appeared in the browser.

During the first attempt, the existing saved-hotel delete endpoint removed that hotel before RAG retrieval. The empty result is recorded below, without claiming success. With explicit approval, the exact inspected hotel/context and nightly values were restored in one transaction: October 10 = 500 cents/10 rooms; October 11 = 10000/5; October 12–14 = 10000/20. Course and conversation records were unchanged by restoration.

### Successful live question

> Show the three cheapest saved hotels near ZIP 16801 with at least one room available for the night of October 11, 2026.

Conversation ID: **`0b0f80b5-a8f6-41f3-b474-949c61e00d00`**. Submitted through the real Vue Ask action; `POST /api/hotel-chat` returned success with state `answer`.

Proposed SQL:

```sql
SELECT DISTINCT h.hotel_id, h.name, n.stay_date, n.nightly_rate_cents, n.rooms_available FROM saved_hotels AS h JOIN saved_hotel_locations AS l ON h.hotel_id = l.hotel_id AND l.requested_zip = ? JOIN demo_hotel_nights AS n ON h.hotel_id = n.hotel_id AND n.stay_date = ? WHERE n.rooms_available >= ? ORDER BY n.nightly_rate_cents ASC LIMIT 3
```

Bound parameters:

```json
[
  "16801",
  "2026-10-11",
  1
]
```

Executed SQL:

```sql
SELECT * FROM (SELECT DISTINCT h.hotel_id, h.name, n.stay_date, n.nightly_rate_cents, n.rooms_available FROM saved_hotels AS h JOIN saved_hotel_locations AS l ON h.hotel_id = l.hotel_id AND l.requested_zip = ? JOIN demo_hotel_nights AS n ON h.hotel_id = n.hotel_id AND n.stay_date = ? WHERE n.rooms_available >= ? ORDER BY n.nightly_rate_cents ASC LIMIT 3) AS rag_rows LIMIT 51
```

Retrieved records:

```json
[
  {
    "hotel_id": "513e06d4fb977553c059209d268568644440f00102f90167bb7e0d00000000920323436f75727479617264206279204d617272696f747420537461746520436f6c6c656765",
    "name": "Courtyard by Marriott State College",
    "stay_date": "2026-10-11",
    "nightly_rate_cents": 10000,
    "rooms_available": 5
  }
]
```

Final answer, as displayed:

> The retrieved saved records show one matching hotel, not three. Courtyard by Marriott State College (hotel ID 513e06d4fb977553c059209d268568644440f00102f90167bb7e0d00000000920323436f75727479617264206279204d617272696f747420537461746520436f6c6c656765) is listed at $100.00 for October 11, 2026, with 5 rooms available. These are simulated classroom rates and availability, not live data. The saved-record retrieval is incomplete evidence and does not establish that no other real hotels exist.
>
> Rates and room availability are simulated classroom data, not live hotel information.

Database comparison: replaying the validated query read-only returned identical records and executed SQL. An independent SQLite join confirmed the same provider hotel ID/name, ZIP `16801`, date `2026-10-11`, rate `10000` cents, and `5` rooms. The answer correctly reported one match rather than inventing three. It included the simulated classroom label and did not claim real booking availability. Retrieval was not truncated. Saved hotels are not complete area inventory.

### Live no-match case

Conversation ID: **`f36b250a-3bce-4346-afa1-c7a2f5316d4c`**. The first live submission asked the same question above while the saved tables were empty following the observed deletion. Both real Responses stages completed; this was a successful empty retrieval, not a model/API failure.

Proposed SQL:

```sql
SELECT DISTINCT h.hotel_id, h.name, h.address, n.stay_date, n.nightly_rate_cents, n.rooms_available FROM saved_hotels AS h JOIN saved_hotel_locations AS l ON h.hotel_id = l.hotel_id JOIN demo_hotel_nights AS n ON h.hotel_id = n.hotel_id AND n.stay_date = ? WHERE l.requested_zip = ? AND n.rooms_available >= ? ORDER BY n.nightly_rate_cents ASC LIMIT 3
```

Parameters: `["2026-10-11", "16801", 1]`.

Executed SQL:

```sql
SELECT * FROM (SELECT DISTINCT h.hotel_id, h.name, h.address, n.stay_date, n.nightly_rate_cents, n.rooms_available FROM saved_hotels AS h JOIN saved_hotel_locations AS l ON h.hotel_id = l.hotel_id JOIN demo_hotel_nights AS n ON h.hotel_id = n.hotel_id AND n.stay_date = ? WHERE l.requested_zip = ? AND n.rooms_available >= ? ORDER BY n.nightly_rate_cents ASC LIMIT 3) AS rag_rows LIMIT 51
```

Retrieved records: `[]`; state: `no_matches`; truncated: `false`.

Displayed answer:

> No matching saved hotel records were retrieved. This does not establish real hotel availability.
>
> Rates and room availability are simulated classroom data, not live hotel information.

The frontend showed “No matching saved records.” It invented no hotel, price, or room count. This documents the database state at that moment; after approved restoration, the same ZIP/date has a saved match. No separate live insufficient-night case was run.

### Persistence and call count

Refreshing Vue restored the successful conversation ID, question, answer, and trace from backend history. After restarting FastAPI, `GET /api/hotel-chat/0b0f80b5-a8f6-41f3-b474-949c61e00d00` returned HTTP 200 with history identical to the captured response. Vue reloaded the same answer after that restart. Saved hotel/night records remained present. History stages: user, proposed_sql, executed_sql, retrieval_result, assistant.

This verification made **two hotel-RAG submissions / four Responses calls**: one live empty result and one successful comparison after restoration. No provider/model change, automatic retry, billing/quota/authentication error, or additional model call for persistence/safety checks occurred.

## MOCKED / FIXTURE SAFETY CHECK

`DELETE FROM saved_hotels` was tested only in temporary test databases with mocked proposals, never against the real course database. The existing SQL-rejection test verified all hotel/course records remained unchanged; the mocked route returned HTTP 422 / `rejected_sql`, with no second model call and no false “no matches” result. Both focused checks passed. Their source is `backend/tests/test_hotel_chat.py`.

Final regression checks: **158 backend tests**, **24 frontend tests**, frontend lint/build, and `git diff --check` passed. One existing Starlette/httpx deprecation warning remains. Installed Node/CLI tools ran lint/build directly because npm is unavailable in the shell. No dependencies or application source changed. Evidence remains uncommitted and unpushed.

### Retained fixed fixture example

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

Fixture tests create temporary conversation UUIDs, persist stages, reopen SQLite, and load history through the endpoint. These fixture examples remain mocked evidence; real conversation IDs are recorded in the live section above.
