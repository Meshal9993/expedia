# Assignment 2, Part 1 evidence log

Final verification: **September 30, 2026** (America/New_York). Branch: `feature/assignment2-part1-live-hotels`. Implementation is complete; this step prepared documentation and evidence only. Application behavior, styling, API contracts, dependency files, tests, and instructor data were unchanged. The existing Assignment 1 `report.md` was left untouched; no Assignment 2 report or commit was created.

## Instructions, changes, and decisions

Instruction summaries below are paraphrases of the project conversation, not invented verbatim prompts. The major implementation instructions are saved in [prompt 05](../prompts/05-assignment2-part1-live-hotels-backend.md) and [prompt 06](../prompts/06-assignment2-part1-live-hotels-view.md).

| Important instruction | Resulting code/design change | Verification | Decision | Limitation or remaining issue |
| --- | --- | --- | --- | --- |
| Research official APIs and sketch before implementation. | [Research](assignment2-part1-research.md), [mockup](assignment2-part1-mockup.md), and [contracts](assignment2-part1-contracts.md). | Compared the documented request/DTO/state plan with the implementation. | Five-digit U.S. ZIP string; geocode then search hotel places within 5 km. | Provider coverage and limit 20 are not exhaustive inventory. |
| Inspect dependencies and wait for approval. | Approved Leaflet 1.9.4 and `httpx==0.28.1`; separate frontend packages and backend virtual environment. | Frontend lint/build and backend imports/tests succeeded. | Reuse httpx; no second HTTP client or unrelated tooling. | npm was initially unavailable on the new Mac; approved Corepack supplied npm. No new installation in this evidence step. |
| Fix the existing annotation failure without changing behavior. | `backend/controllers/database.py` imports `typing.List`; later `search_hotel_stays` annotation uses `List[HotelStay]`. | Test collection recovered; final full suite passes. | Keep the public `DatabaseController.list` method, SQL, and CRUD unchanged. | The class method named `list` had shadowed the builtin in the later annotation. Initial test collection failed and was corrected narrowly. |
| Implement only the backend under MVC (prompt 05). | `backend/config.py`, `models/live_hotels.py`, `controllers/location.py`, and thin route in `main.py`; mocked tests in `tests/test_live_hotels.py`. | Mocked ZIP, mapping, error, and credential-safety checks; earlier live API-body checks. | Return provider-backed location DTOs; distinguish empty success from unresolved ZIP/provider/quota errors. | Missing names use `Name unavailable`; missing addresses are omitted; no invented hotel fields. |
| Add Vue and Leaflet without exposing the key (prompt 06). | `LiveHotelSearch.vue`, `HotelMap.vue`, `App.vue`, and CSS. | Live browser searches, synchronized selection, keyboard use, and responsive layout. | One shared `selectedHotelId`; OpenStreetMap tiles and visible attribution. | No room availability or booking connection for live places; no real-device/screen-reader audit. |
| Simplify the polished presentation without changing functionality. | Light background, smaller heading, simple buttons/borders; decorative eyebrow and list badges removed. | Live searches/selection, lint/build, backend suite, and whitespace checks repeated. | Keep the accepted student-project styling and all feedback states. | Earlier polished screenshots are not used as final styling evidence. |
| Prepare final evidence; do not edit behavior, write report, or commit. | This log, updated handoff/reference docs, and browser verification; the student later chose video-only Part 1 media evidence. | Final checks below; source/style/manifest/test/CSV hashes compared before and after. | Document current results and clearly label historical checks. | No exact model variant is inferred; the student supplied the Codex disclosure below and confirmed the evidence was complete. |

## Final verification performed

The running local frontend (`http://127.0.0.1:5173/`) and backend (`http://127.0.0.1:8000`) were reused. Two live ZIP searches were made through the Vue form and our backend; no mock provider was active for those searches.

| Check | Expected | Observed |
| --- | --- | --- |
| Live `16801` | Matching ZIP summary and provider hotel list/map. | State College, Pennsylvania; 15 hotel places; list and markers displayed. |
| Live `02108` | Preserve the leading zero as text. | Input and heading showed `02108`; Boston, Massachusetts; 20 hotel places, including one `Name unavailable`. |
| List → map | Same hotel selected in both representations. | Keyboard-selected Ramada State College row opened its matching selected-marker popup; focus was visible. |
| Map → list | Marker selects and reveals corresponding row. | The Penn Stater Hotel & Conference Center marker selected/scrolled to its row and opened its popup. |
| Invalid `1234` | Useful local feedback; no stale results. | Five-digit instruction, `aria-invalid=true`, zero old hotel cards and maps. Code and mocked tests establish rejection before a provider call. |
| Layout/attribution | Desktop side by side; mobile stacked; credits visible. | Verified at 1280px and 390px. Mobile page width matched viewport width; map/data credits visible. |
| Assignment 1 regression | Original hotel-name search still returns supplied stays. | `Harbor Lantern Hotel`: Boston Harbor Weekend and Boston Autumn Weekend, two stays. Booking history loaded. |
| Frontend lint | Pass. | `npm run lint`: exit 0. |
| Frontend production build | Pass. | `npm run build`: exit 0. |
| Full backend suite | All existing and new tests collect/run. | `backend/.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider`: **40 passed**, one existing Starlette/httpx deprecation warning. |
| Whitespace | No diff errors. | `git diff --check`: exit 0. |
| Secrets and scope | Local key stays untracked; application files unchanged. | `git check-ignore -v backend/.env` matched `.gitignore:16`; `git ls-files` and status did not include the file. Source/style/manifest/test/CSV hashes stayed identical. The key was not displayed. |

The npm scripts ran using the already-approved cached npm 12.1.0 CLI and Node runtime. No packages were installed. Observed counts are not assertions for future live tests, and reaching 20 does not prove only 20 hotels exist.

Earlier September 30 live API-body verification confirmed requested/resolved postcode equality, valid provider coordinates/identifiers, and no invented price/rating/availability/booking fields. Recorded centers were `16801`: `(40.790200114, -77.848551881)` and `02108`: `(42.357581412, -71.065946589)`. These are earlier observations, not fresh response-body captures from the final browser pass.

The backend suite rerun here mocks empty Places success, mismatched/unresolved ZIPs, missing names/addresses, invalid coordinates, missing configuration, provider failures, and rate limits. Earlier browser mocks checked loading, empty, unresolved, service-failure, and temporary-limit feedback; they were stopped afterward. Those browser mocks were not repeated in this final pass. No intentional live quota exhaustion occurred. Booking mutations, real devices, screen readers, and other browser engines were not retested.

## Evidence files

The student intentionally deleted the Part 1 screenshots and requested that only the demo video be retained as Part 1 media evidence. The live/browser observations above remain the verification record; no deleted screenshot is required or linked.

| File | Evidence/status |
| --- | --- |
| [September 30 demo recording](<screenshots/Screen Recording 2026-09-30 at 7.14.18 PM.mov>) | QuickTime MOV, about 78 MiB; retained at the student's request. Playback/content was not independently reviewed during automated verification. |

No new demo video was recorded or edited during evidence preparation. Before the final commit, lint, build, all 40 backend tests, and the requested live/browser checks passed again. The student confirmed the evidence and AI disclosure were complete and authorized committing, merging, and pushing; the Assignment 2 report remains a separate task.

Earlier Assignment 1 assets were preserved: [search success](screenshots/search-success.png), [no results](screenshots/search-no-results.png), and [September 21 recording](<screenshots/Recording 2026-09-21 210541.mp4>). The `.mp4` currently contains a 134-byte Git LFS pointer, not the video payload, so it is not playable from this checkout. It is not counted as a playable Part 1 demo.

## AI disclosure

**Verified tool:** OpenAI **Codex**, used in the desktop app for this project/session. The session describes the assistant as based on **GPT-6**; that identifies a family, not a verifiable exact selected model ID/version for every earlier step. No model variant is inferred from the list of available tools/models.

**Student to complete before submission:**

- Exact model identifier/version shown for the work: **[fill in from the app/session record]**.
- Any other AI tools/models used in earlier work: **[list verified names, or confirm none]**. This project record cannot establish them.

AI assisted with research and document planning; MVC/API contract planning; backend DTO/controller/route implementation and mocked tests; Vue/Leaflet implementation and the requested styling revision; automated lint/build/pytest checks; browser verification; and evidence/handoff documentation. The student provided scope, constraints, dependency approvals, acceptance, and revision instructions. AI-generated work was checked against the implementation and the recorded tests; those checks do not replace the student's responsibility to understand and review the submission.

The disclosure's verified information and manual placeholders are intentionally separate. Do not replace the placeholders with guessed model names. The assignment report remains pending a separate request.

## AI Disclosure

### Codex

I used Codex to help inspect and edit the project code, run tests, and verify the application.

I also used Codex's annotate/comment feature to point directly to parts of the interface that I wanted to review or change. This helped me give focused feedback without changing unrelated parts of the page.
