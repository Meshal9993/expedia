# Chat connection contract

This first integration step adds general OpenAI chat. It does not query SQLite or implement the planned RAG workflow yet. Existing hotel, local-storage, and booking contracts are unchanged.

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

Mocked checks cover history, text/refusal streaming, malformed/interrupted replies, invalid input, missing configuration, authentication/service failure, quota/rate limits, and credential-safe errors. On October 6, 2026, a live request reached OpenAI but returned `credit_balance_exhausted`; model access succeeded, and no live reply was generated. This condition maps to the safe `limited` event. Live reply verification remains pending API credits. The two-request, validated read-only SQLite RAG flow remains the next stage.
