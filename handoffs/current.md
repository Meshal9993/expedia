# Current handoff

## Assignment 2, Part 2: revised OpenAI RAG implementation

October 8, 2026, on `rag_integration`, based on basic chatbot checkpoint `4447dd72ff975cd9cfd525448969999fe52363aa`. The class foundation is OpenAI; no OpenRouter replacement or new dependency was added. Basic `/api/chat`, Assignment 1, and Part 1/local-storage APIs remain intact.

Added hotel prompt/DTOs, `POST /api/hotel-chat`, two Responses stages, restricted read-only SQL retrieval, and separate persistent conversation/event stages. Vue shows answer/status/trace and restores the browser's conversation ID from backend history. Generated SQL cannot access history or course booking/user tables. Multi-night totals/coverage use required nightly rows, exclude checkout, and label rates/rooms simulated classroom data.

The fixed fixture and [context example](../docs/assignment2-part2-rag-context.md) are explicitly mocked/test evidence. Tests use temporary databases; the real course database is not replaced. No live OpenAI RAG call, commit, or push was performed in this implementation step. Next: review, restart the project, verify model access/credits, then authorize a live RAG demonstration and record its real conversation ID.

Final checks: 158 backend tests and 24 frontend tests passed; frontend lint/build and `git diff --check` passed. Backend tests reported one existing Starlette/httpx deprecation warning. npm is unavailable in the current shell, so the existing Node runtime ran the installed lint/build CLIs directly. Credential review found no keys in the tracked diff or new files; `backend/.env` is ignored and untracked. The output-limit edge case was corrected to show insufficient data when no complete record fits.

## Assignment 2, Part 2: first OpenAI chat connection

October 6, 2026, on `rag_integration`: added general chat through Vue → `POST /api/chat` → `ChatController` → OpenAI Responses, using existing `httpx` and the supplied `gpt-5.6-luna`. Configuration stays in ignored `backend/.env`; no new dependencies were installed. The local-storage checkpoint is preserved in `3de2f9867aa37913c62dc519f7750599ba6f0b1f`, with the earlier RAG planning documents in `9679d0dc7b7d001c4277dfa1e122999a773b622e`.

Checks: 105 backend tests and 16 frontend HTTP workflow tests passed; installed lint tools and the Vite production build passed; `git diff --check` passed. Browser checks covered mocked streaming, follow-up history, keyboard submission, quota feedback, saved ZIP `16801` with map selection, and Assignment 1's two Harbor Lantern stays. Temporary chat mocks are restored to normal provider behavior after verification.

The October 6 basic live request returned `credit_balance_exhausted`; no real reply was generated. This is historical evidence, not a current credit check. That basic step did not retrieve records or implement RAG. It was saved in checkpoint `4447dd72ff975cd9cfd525448969999fe52363aa` and remains unpushed. See [contracts](../docs/chat-contract.md).

## Assignment 2, Part 1: complete and published

Final evidence verification: **September 30, 2026**, on `feature/assignment2-part1-live-hotels`. The assessed implementation commit is `85d0ac345a451267742c456a3d1ee70e524e3f72`, merged into `main` and pushed on both branches to [Meshal9993/expedia](https://github.com/Meshal9993/expedia). The [final report](../report.md) was added and pushed to `main` in the separate report-only commit `49962a4f0b4d4d368233cfa851f65d470b2881b8`. Local URLs are frontend `http://127.0.0.1:5173/` and backend `http://127.0.0.1:8000`.

- FastAPI provides `GET /api/live-hotels?zip=<five-digit ZIP>`. `backend/controllers/location.py` validates the ZIP, confirms the matching U.S. postcode, requests Geoapify hotel places within 5,000 meters (limit 20), and maps only provider-backed fields to separate DTOs.
- `frontend/src/components/LiveHotelSearch.vue` owns the ZIP string, HTTP request, feedback states, results, and shared `selectedHotelId`. `HotelMap.vue` owns Leaflet rendering and lifecycle. List and marker selection stay synchronized.
- The approved dependencies are `httpx==0.28.1` in `backend/.venv` and Leaflet 1.9.4 in the frontend. No dependencies were installed during evidence preparation.
- The final visual revision uses a light background, smaller headings, basic buttons and bordered rows, with clear selected/focus states. Behavior, API contracts, Leaflet behavior, accessibility controls, and responsive layouts were preserved. Do not change this accepted interface without a new request.
- `backend/.env` remains ignored and untracked. Its value was not displayed. The key stays server-side; OpenStreetMap tiles do not use it.
- [Research](../docs/assignment2-part1-research.md), [early mockup](../docs/assignment2-part1-mockup.md), and [contracts](../docs/assignment2-part1-contracts.md) match the implementation. The [evidence log](../docs/assignment2-part1-evidence.md) contains the prompt/change/decision record, final media inventory, AI disclosure, and limitations.

## Final verification

The existing project servers were reused at `http://127.0.0.1:5173/` and `http://127.0.0.1:8000`. The backend runs without file watching because `--reload` was blocked in this local environment; README documents the fallback.

| Check | Observed result |
| --- | --- |
| Live ZIP `16801` | State College, Pennsylvania; 15 hotel places in this observation. |
| Live ZIP `02108` | Boston, Massachusetts; 20 hotel places in this observation. Input and heading preserved the leading zero; one place displayed `Name unavailable`. |
| List → map | Selecting Ramada State College opened its matching popup and selected marker. Keyboard selection and visible focus worked. |
| Map → list | Selecting The Penn Stater Hotel & Conference Center marker selected and scrolled to the matching row. |
| Invalid ZIP `1234` | Validation feedback appeared, `aria-invalid` was true, and previous results/map were removed. |
| Responsive layout | Desktop 1280px: list/map side by side. Narrow 390px: stacked, no horizontal page overflow; attribution visible. |
| Assignment 1 name search | `Harbor Lantern Hotel` returned Boston Harbor Weekend and Boston Autumn Weekend. Booking history loaded. |
| Frontend | `npm run lint` and `npm run build` passed. |
| Backend | Full suite: 40 passed; one existing Starlette/httpx deprecation warning. |
| Repository | `git diff --check` passed. Source, styling, dependencies, tests, and instructor CSV hashes were unchanged by evidence preparation. `.env` remained ignored and untracked. |

Hotel counts are observations, not future test assertions or exhaustive inventory totals. These are location results, not room availability, prices, ratings, or booking offers.

Earlier backend live verification on **September 30, 2026** established requested/resolved postcode equality and provider coordinates: `16801` at `(40.790200114, -77.848551881)` and `02108` at `(42.357581412, -71.065946589)`. These coordinates are the earlier observation, not a fresh API-body capture in this final browser pass. An earlier prompt requested September 29 as a label; the actual verification date was September 30.

The full backend suite covers mocked empty results, unresolved/mismatched ZIPs, missing provider fields, configuration errors, provider failures, rate limits, and safe responses. Earlier isolated browser mocks verified loading, empty, unresolved, service-failure, and temporary-limit messages; those mock servers were stopped. This final pass did not repeat those browser mocks or deliberately trigger a live quota error.

## Assignment 1 baseline preserved

The SQLite hotel-name search, available stays, demo-traveler bookings, booking history/filter, cancellation, and confirmed deletion remain separate from live places. Only `DatabaseController` owns SQL and CSV import. The local ignored SQLite database seeds instructor CSVs once and never writes changes back to them.

Earlier Assignment 1 browser checks covered booking persistence across restart, cancellation retention, deletion of a temporary booking, and no-results feedback. The final pass repeated name search and history loading; it did not create/cancel/delete bookings. Existing backend tests still cover those behaviors.

## Evidence and next step

The student intentionally removed the Part 1 screenshots and requested video-only media evidence. The existing September 30 `.mov` is indexed in the [evidence log](../docs/assignment2-part1-evidence.md); deleted screenshot references have been removed. Earlier Assignment 1 screenshots were preserved. The older `.mp4` is a Git LFS pointer in this checkout, not playable local video content.

The student confirmed the evidence and Codex disclosure are complete. Only an exact model identifier remains a manual placeholder if the assignment requires one; no model name is guessed. The MOV's playback/content was not independently reviewed during automated verification. Real-device/screen-reader testing and a broader browser matrix were not performed.

The implementation, evidence, and report are published. This documentation consistency review changes no application code or recorded results and must remain uncommitted until reviewed.
