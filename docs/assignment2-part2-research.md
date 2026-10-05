# Assignment 2 Part 2: RAG planning

Inspection date: October 5, 2026. This is a plan only; no chatbot is implemented and no new dependencies are installed.

## Revised workflow

1. The user asks a hotel/date question in Vue.
2. FastAPI passes the question and allowed local schema to the **first LLM request**, which proposes SQL.
3. The backend validates that SQL before allowing retrieval.
4. `DatabaseController` runs a bounded, read-only SQLite query and returns matched records.
5. The **second LLM request** receives the question and retrieved records, with instructions to use only that evidence.
6. Vue shows the grounded answer and, optionally, the matched hotel/date information.

Retrieval uses the existing `saved_hotels`, `saved_hotel_locations`, and `demo_hotel_nights` tables. Their joins use the preserved provider ID. ZIP codes stay strings, including leading zeros. Rates and room counts are simulated course data, never verified hotel prices or real availability. A missing name/address stays missing; an empty match must be explained honestly.

## Planned boundaries and checks

- Keep the LLM orchestration in a backend controller, SQL access in `DatabaseController`, DTOs in models, and presentation in Vue. Keep Assignment 1 and the frozen Part 1 API unchanged.
- Treat generated SQL as untrusted. Plan for one read query over allowed tables/columns/functions, rejecting writes, multiple statements, `ATTACH`, and model-supplied `PRAGMA` commands. A simple `SELECT` prefix check is insufficient.
- Use a read-only connection plus an authorizer and row/execution limits. SQLite supports [read-only URI connections](https://www.sqlite.org/uri.html) and [authorization callbacks](https://www.sqlite.org/c3ref/set_authorizer.html); Python exposes [authorizers](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.set_authorizer) and [progress handlers](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.set_progress_handler).
- Distinguish no matches, insufficient stored data, rejected SQL, and service failure. Answers must not invent missing information or describe saved hotels as complete local inventory.
- Keep provider credentials on the backend and out of prompts, responses, logs, and Git. Send only the question, allowed schema, and necessary retrieved hotel/date data to the LLM.

## Current readiness

Local save/remove, ZIP associations, dated demo nights, and local-first lookup exist and pass automated checks. `httpx==0.28.1` is already declared; Python `sqlite3` is available. The existing environment helper handles Geoapify only. No LLM client, chatbot, or generated-SQL validator was found. LLM provider/model selection, configuration, and any dependency review/approval remain future work.
