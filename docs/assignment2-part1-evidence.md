# Assignment 2, Part 1 evidence log

Final verification: **September 30, 2026** (America/New_York). Work was completed on `feature/assignment2-part1-live-hotels` and merged into `main`; both branches were pushed to [Meshal9993/expedia](https://github.com/Meshal9993/expedia). The assessed implementation commit is `85d0ac345a451267742c456a3d1ee70e524e3f72`. The [final report](../report.md) was added separately in `49962a4f0b4d4d368233cfa851f65d470b2881b8`. Documentation reviews do not change application behavior or the recorded test results.

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
| Prepare final evidence before writing the report or committing. | This log, updated handoff/reference docs, and browser verification; the student later chose video-only Part 1 media evidence. | Final checks below; source/style/manifest/test/CSV hashes compared before and after evidence preparation. | Document results and clearly label historical checks. | No exact model ID is recorded; the student supplied the Codex disclosure below and confirmed the evidence was complete. |
| Commit and publish the completed work, then add the finished report separately. | Implementation commit `85d0ac3` and report-only commit `49962a4`. | Both implementation branches were verified on GitHub; the report was pushed to `main`; Git status was clean after each push. | Preserve the feature branch and assess the implementation at `85d0ac3`. | GitHub accepted the retained MOV with a file-size warning. |

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

No new demo video was recorded or edited during evidence preparation. Before the implementation commit, lint, build, all 40 backend tests, and the requested live/browser checks passed again. The student confirmed the evidence and AI disclosure were complete. The implementation and the separate finished report have since been committed and pushed.

Earlier Assignment 1 assets were preserved: [search success](screenshots/search-success.png), [no results](screenshots/search-no-results.png), and [September 21 recording](<screenshots/Recording 2026-09-21 210541.mp4>). The `.mp4` currently contains a 134-byte Git LFS pointer, not the video payload, so it is not playable from this checkout. It is not counted as a playable Part 1 demo.

## AI disclosure

I used Codex to help inspect and edit the project code, run tests, and verify the application.

I also used Codex's annotate/comment feature to point directly to parts of the interface that I wanted to review or change. This helped me give focused feedback without changing unrelated parts of the page.

Codex also helped with research and document planning, MVC/API contracts, backend implementation and mocked tests, Vue/Leaflet implementation, and automated and browser verification. I provided the instructions, approvals, and feedback and reviewed the results.

**Verified tool:** OpenAI Codex desktop app. The exact model identifier for the earlier work is not recorded. If required for submission: **[fill in the exact model from the app/session record]**. No model name is guessed.
