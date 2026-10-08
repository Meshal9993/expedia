# Assignment 2 Part 2: RAG planning

Started October 5; RAG implemented October 8, 2026 on `rag_integration`, after basic chatbot checkpoint `4447dd72ff975cd9cfd525448969999fe52363aa`. The class workflow uses OpenAI, not OpenRouter. No new dependencies were installed.

## Revised workflow

1. The user asks a hotel/date question in Vue.
2. FastAPI passes the question, hotel prompt, and allowed schema to the **first OpenAI request**, which proposes SQL, parameters, and optional stay dates.
3. The backend validates that SQL before allowing retrieval.
4. `DatabaseController` runs a bounded, read-only SQLite query and returns matched records.
5. The **second LLM request** receives the question and retrieved records, with instructions to use only that evidence.
6. Vue shows the grounded answer and an expandable SQL/parameters/records trace. SQLite saves the conversation stages; browser storage keeps only its ID for refresh restoration.

Retrieval uses the existing `saved_hotels`, `saved_hotel_locations`, and `demo_hotel_nights` tables. Their joins use the preserved provider ID. ZIP codes stay strings, including leading zeros. Rates and room counts are simulated course data, never verified hotel prices or real availability. A missing name/address stays missing; an empty match must be explained honestly.

## Decisions and limits

- Keep the LLM orchestration in a backend controller, SQL access in `DatabaseController`, DTOs in models, and presentation in Vue. Keep Assignment 1 and the frozen Part 1 API unchanged.
- Treat generated SQL as untrusted even when JSON is valid. Use one SELECT with raw columns including hotel_id, bound filter values, and exact hotel-ID joins. Reject writes, comments, multiple statements, unapproved access, and unsafe functions. The small grammar deliberately excludes aggregates, computed projections, subqueries, and CROSS/OR/self joins. Unsupported queries receive a rejection, not an invented answer.
- Use a read-only connection plus an authorizer and row/execution limits. SQLite supports [read-only URI connections](https://www.sqlite.org/uri.html) and [authorization callbacks](https://www.sqlite.org/c3ref/set_authorizer.html); Python exposes [authorizers](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.set_authorizer) and [progress handlers](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.set_progress_handler).
- Distinguish no matches, insufficient stored data, rejected SQL, and service failure. Answers must not invent missing information or describe saved hotels as complete local inventory.
- Keep provider credentials on the backend and out of prompts, responses, logs, and Git. Send only the question, allowed schema, and necessary retrieved hotel/date data to the LLM.
- Reuse `httpx==0.28.1`, OpenAI Responses, the configured `gpt-5.6-luna`, `store=false`, no tools, and finite limits. [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses) supplies JSON structure; backend checks still establish SQL safety.
- Retrieval returns at most 50 rows/32 KiB with a one-second SQL deadline. Truncation is incomplete evidence. Separate fixed application SQL writes history; model queries cannot read/write it.
- Checkout is excluded. The backend proves each required night's coverage and computes per-room totals in cents. Missing nights mean unknown availability/total; model prose cannot override stay checks. Ordinary answers use checked hotel-ID citations and still need factual review during live verification.

## Current readiness

Basic `/api/chat` remains available; hotel RAG uses `/api/hotel-chat`. Assignment 1, ZIP search, local Add/Remove, and list/map remain separate. See [contracts](chat-contract.md), [fixed fictional fixture](assignment2-part2-rag-fixture.json), and [mocked context example](assignment2-part2-rag-context.md). No live OpenAI RAG request has been made. Access/credits and live evidence remain to be verified.
