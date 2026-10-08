# Chat connection contract

Basic OpenAI chat is preserved in checkpoint `4447dd72ff975cd9cfd525448969999fe52363aa`. Separate hotel RAG was added October 8, 2026. Existing hotel, local-storage, and booking contracts are unchanged.

## MVC and configuration

`backend/models/chat.py` defines messages and stream events. `ChatController` in `backend/controllers/chat.py` uses the existing `httpx` dependency. The thin FastAPI route is `POST /api/chat`. Vue's `ChatAssistant.vue` and `api/chat.js` display plain text, retain successful turns in memory, and show loading/error feedback.

The backend reads `OPENAI_API_KEY` from its process environment or ignored `backend/.env` using an explicit path. `OPENAI_MODEL` is optional and defaults to the supplied `gpt-5.6-luna`. Environment-file edits are read on the next request; process-environment or Python-source changes require a backend restart. Keys, raw provider errors, and reasoning events are never forwarded to Vue. No SDK or other dependency was added.

## HTTP contract

Request: `{"messages":[{"role":"user","content":"Hello"}]}`. Messages alternate user/assistant, starting and ending with user. Maximum: 21 messages, 4,000 characters per user question, and 24,000 characters total. Client-supplied system messages, keys, and unknown fields are rejected with `422` before a provider call. Conversation history is sent explicitly, with no persistent browser storage.

Response: newline-delimited JSON (`application/x-ndjson`):

```json
{"type":"delta","text":"Hello"}
{"type":"done","text":""}
```

A missing local key returns HTTP `503` with `{"detail":"Chat service is not configured."}`. After streaming begins, failures use `{"type":"error","text":"","code":"..."}` with one of `configuration`, `limited`, `timeout`, `unavailable`, or `incomplete`. The View shows a fixed friendly message and marks partial answers incomplete. Failed turns are excluded from later conversation requests.

## Provider request and checks

The backend calls OpenAI `/v1/responses` with the supplied model, default service tier, medium verbosity/reasoning effort, no tools, streaming enabled, `store=false`, and a 4,096-token output limit. It forwards output-text/refusal deltas and requires explicit completion. Connection/write/pool timeouts are 10 seconds, read inactivity is 60 seconds, and a 120-second deadline is checked between stream events. Vue aborts after 130 seconds and on unmount. No automatic retries are made.

The [model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-luna) and [Responses streaming guide](https://developers.openai.com/api/docs/guides/streaming-responses) informed the request. The reference sample's optional stored reasoning and web-search source fields are unnecessary for this plain-text connection.

Mocked checks cover history, text/refusal streaming, malformed/interrupted replies, invalid input, missing configuration, authentication/service failure, quota/rate limits, and credential-safe errors. The October 6 basic live request returned `credit_balance_exhausted`, with no real reply. This is historical evidence, not a new account-status check. No live hotel RAG request has been made.

## Hotel RAG contract

`POST /api/hotel-chat`: `{"question":"Which saved hotels in ZIP 02108 have rooms from 2026-10-10 to 2026-10-13?","conversation_id":null}`. Question: nonblank text, at most 4,000 characters; optional ID: UUID. Client SQL, keys, and extra fields are rejected.

Success contains `conversation_id`, `question`, `proposed_sql`, `executed_sql`, `parameters`, `retrieved_records`, `answer`, `state`, `truncated`, `stay_assessments`, `simulated_data:true`. State: `answer`, `no_matches`, or `insufficient_data`. No full provider response or credentials are returned.

`GET /api/hotel-chat/{conversation_id}` returns conversation metadata and recent ordered events: at most 100 events/512 KiB of content, with `truncated` when needed. Older history remains stored. Vue persists only the ID and restores history on mount. New conversation starts another ID without deleting old history. Each question performs fresh retrieval; include its ZIP/dates explicitly.

Safe error JSON: `{"code":"...","detail":"...","conversation_id":"..."}`; ID appears after conversation creation. Invalid input/rejected SQL: 422; missing conversation: 404; configuration/retrieval/history failure: 503; model failure/invalid answer: 502; rate/quota limit: 429; timeout: 504. A failed answer request retains retrieval evidence, available with Reload history. Errors never mean “no hotels found.”

## Hotel RAG MVC and safety

`models/hotel_chat.py` defines the DTOs. `HotelChatController` loads root `prompts/hotel-assistant.md` through an explicit path and orchestrates two public `ChatController.request_output` calls. Routes are thin; only `DatabaseController` owns SQLite I/O.

The first Responses call requires strict JSON `{sql,parameters,stay}`; stay is null or `{check_in,check_out,rooms}`. The second requires `{answer,hotel_ids}` and receives the original question, exact query context, retrieved rows, and checked stay assessments. Both reuse httpx/model configuration, with no tools, `store=false`, 4,096 output tokens, 40-second read inactivity, and a 50-second request deadline. Vue aborts a RAG request after 120 seconds.

`DatabaseController.retrieve_hotel_records(SqlProposal) -> HotelRetrieval` requires a single SELECT, explicit raw approved columns including hotel_id, unique output names, real hotel-ID joins, and bound filter values. Reject comments, literals, writes, transactions, schema/system/history access, unsafe functions, aggregates, computed projections, subqueries, and CROSS/OR/self joins. Only lower/upper/coalesce/LIKE filter functions are allowed. SQLite's authorizer enforces actual table/column access. Retrieval uses `mode=ro`, `query_only`, closed connections, and a one-second progress-handler deadline. A backend wrapper fetches at most 51 rows to detect truncation, returning at most 50/32 KiB.

For stays, require every date in `[check_in,check_out)`. Deduplicate nightly evidence; missing/conflicting dates produce null total/availability. Complete totals are per room, computed from stored cents. The backend renders checked stay summaries rather than trusting model arithmetic. Empty/truncated/missing-night results cannot be overridden with positive model claims. Other model prose uses the grounding prompt and checked ID citations; factual live review remains necessary.

## Trace storage

Repeatable initialization adds `chat_conversations(conversation_id,created_at,updated_at,prompt_hash,prompt_version)` and `chat_events(event_id,conversation_id,turn_id,timestamp,stage,content)`. Content is bounded JSON; event IDs preserve order and conversation foreign keys are enforced. Stages: user, proposed_sql, executed_sql, retrieval_result, retrieval_error, model_error, assistant. User events also record model and per-turn prompt hash/version. Error stages contain safe codes, not raw exceptions.

Public database methods `create_chat_conversation(ChatPromptMetadata) -> ChatConversation`, `append_chat_event(ChatEventWrite) -> ChatHistoryEvent`, and `get_chat_history(UUID) -> ChatHistory` use DTOs and fixed parameterized application SQL, separately from hotel retrieval. Generated queries cannot read/write history. Reopening SQLite preserves it; a failed history write returns an error rather than claiming success. A record that exceeds the retrieval output limit produces insufficient data, even when no complete rows fit.

The [fixture](assignment2-part2-rag-fixture.json) is fictional and loaded only into temporary test databases. See [the context example](assignment2-part2-rag-context.md). The real course database is not replaced.
