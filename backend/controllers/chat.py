"""OpenAI Responses transport. Local-record RAG is a separate next step."""

import json
from contextlib import AsyncExitStack
from time import monotonic
from typing import AsyncIterator

import httpx

from backend.config import get_openai_api_key, get_openai_model
from backend.models.chat import ChatEvent, ChatRequest


RESPONSES_URL = "https://api.openai.com/v1/responses"
TIMEOUT = httpx.Timeout(60.0, connect=10.0, write=10.0, pool=10.0)
INSTRUCTIONS = (
    "You are the Booking classroom project's general chat assistant. "
    "Answer clearly and briefly. You have no access to its local database, "
    "saved hotels, current hotel inventory, or real room availability. "
    "Do not claim you retrieved records, performed a booking, or know live "
    "hotel prices or availability. Explain that local-data retrieval is not "
    "connected when a question requires those records."
)


class ChatConfigurationError(Exception):
    """A required backend setting is missing."""


class ChatController:
    def __init__(self, client: httpx.AsyncClient | None = None,
                 api_key: str | None = None, model: str | None = None):
        self.client = client
        self.api_key = get_openai_api_key() if api_key is None else api_key
        self.model = get_openai_model() if model is None else model

    def ensure_configured(self) -> None:
        if not self.api_key or not self.api_key.strip():
            raise ChatConfigurationError

    @staticmethod
    def _provider_error(event: dict) -> ChatEvent:
        error = event.get("error") or event.get("response", {}).get("error") or event
        code = error.get("code") if isinstance(error, dict) else None
        if code in ("rate_limit_exceeded", "insufficient_quota", "credit_balance_exhausted"):
            state = "limited"
        elif code in ("invalid_api_key", "model_not_found"):
            state = "configuration"
        else:
            state = "unavailable"
        return ChatEvent(type="error", code=state)

    async def stream_reply(self, request: ChatRequest) -> AsyncIterator[ChatEvent]:
        """Yield only text and safe terminal events; never raw provider errors."""
        self.ensure_configured()
        payload = {
            "model": self.model,
            "service_tier": "default",
            "instructions": INSTRUCTIONS,
            "input": [message.model_dump() for message in request.messages],
            "text": {"format": {"type": "text"}, "verbosity": "medium"},
            "reasoning": {"effort": "medium"},
            "tools": [],
            "stream": True,
            "store": False,
            "max_output_tokens": 4096,
        }
        started = monotonic()
        has_text = False
        try:
            async with AsyncExitStack() as stack:
                client = self.client or await stack.enter_async_context(httpx.AsyncClient(timeout=TIMEOUT))
                response = await stack.enter_async_context(client.stream(
                    "POST", RESPONSES_URL, json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}, timeout=TIMEOUT,
                ))
                if response.status_code != 200:
                    state = {401: "configuration", 403: "configuration", 429: "limited"}.get(
                        response.status_code, "unavailable",
                    )
                    yield ChatEvent(type="error", code=state)
                    return
                async for line in response.aiter_lines():
                    if monotonic() - started > 120:
                        yield ChatEvent(type="error", code="timeout")
                        return
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    event = json.loads(data)
                    if not isinstance(event, dict):
                        raise ValueError("Invalid stream event")
                    kind = event.get("type")
                    if kind in ("response.output_text.delta", "response.refusal.delta"):
                        delta = event.get("delta")
                        if not isinstance(delta, str):
                            raise ValueError("Invalid text event")
                        has_text = has_text or bool(delta.strip())
                        yield ChatEvent(type="delta", text=delta)
                    elif kind == "response.completed":
                        yield ChatEvent(type="done") if has_text else ChatEvent(type="error", code="unavailable")
                        return
                    elif kind in ("error", "response.failed"):
                        yield self._provider_error(event)
                        return
                    elif kind == "response.incomplete":
                        yield ChatEvent(type="error", code="incomplete")
                        return
                yield ChatEvent(type="error", code="incomplete")
        except httpx.TimeoutException:
            yield ChatEvent(type="error", code="timeout")
        except (httpx.HTTPError, ValueError, TypeError, AttributeError):
            yield ChatEvent(type="error", code="unavailable")
