"""Chat transport checks use a mocked provider, never real credentials/quota."""

import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from backend import config
from backend.controllers.chat import ChatController
from backend.main import app, get_chat_controller


TEST_KEY = "mock-openai-key"
QUESTION = {"messages": [{"role": "user", "content": "Hello"}]}


def sse(*events):
    return "".join("data: " + json.dumps(event) + "\n\n" for event in events)


def text_stream(*parts):
    return sse(
        {"type": "response.created"},
        *({"type": "response.output_text.delta", "delta": part} for part in parts),
        {"type": "response.completed", "response": {"status": "completed"}},
    )


@pytest.fixture
def route():
    requests = []

    def invoke(provider_response, payload=None, api_key=TEST_KEY):
        def respond(request):
            requests.append(request)
            return provider_response(request) if callable(provider_response) else provider_response
        provider = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        app.dependency_overrides[get_chat_controller] = lambda: ChatController(
            client=provider, api_key=api_key, model="gpt-5.6-luna",
        )
        try:
            with TestClient(app) as client:
                response = client.post("/api/chat", json=payload or QUESTION)
        finally:
            app.dependency_overrides.clear()
            asyncio.run(provider.aclose())
        return response

    try:
        yield invoke, requests
    finally:
        app.dependency_overrides.clear()


def events(response):
    return [json.loads(line) for line in response.text.splitlines() if line]


def test_route_streams_text_and_forwards_only_bounded_history(route):
    invoke, requests = route
    payload = {"messages": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": "Can you see my saved hotels?"},
    ]}
    response = invoke(httpx.Response(200, text=text_stream("No local ", "data is connected.")), payload)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert events(response) == [
        {"type": "delta", "text": "No local "},
        {"type": "delta", "text": "data is connected."},
        {"type": "done", "text": ""},
    ]
    assert response.headers["cache-control"] == "no-store"
    assert len(requests) == 1
    request = requests[0]
    sent = json.loads(request.content)
    assert str(request.url) == "https://api.openai.com/v1/responses"
    assert request.headers["authorization"] == "Bearer " + TEST_KEY
    assert sent["input"] == payload["messages"]
    assert sent["model"] == "gpt-5.6-luna"
    assert sent["stream"] is True and sent["store"] is False
    assert sent["tools"] == []
    assert sent["reasoning"] == {"effort": "medium"}
    assert sent["max_output_tokens"] == 4096
    assert request.extensions["timeout"]["read"] == 60
    assert TEST_KEY not in request.content.decode() + response.text


@pytest.mark.parametrize("status,code", [(401, "configuration"), (403, "configuration"), (429, "limited"), (500, "unavailable"), (400, "unavailable")])
def test_http_failures_never_expose_provider_errors(route, status, code):
    invoke, _ = route
    response = invoke(httpx.Response(status, json={"error": {"message": TEST_KEY}}))
    assert events(response) == [{"type": "error", "text": "", "code": code}]
    assert TEST_KEY not in response.text


@pytest.mark.parametrize("kind", ["error", "response.failed"])
@pytest.mark.parametrize("code", ["insufficient_quota", "credit_balance_exhausted"])
def test_stream_failure_does_not_return_raw_error(route, kind, code):
    invoke, _ = route
    error = {"code": code, "message": TEST_KEY}
    event = {"type": kind, "error": error} if kind == "error" else {"type": kind, "response": {"error": error}}
    response = invoke(httpx.Response(200, text=sse(event)))
    assert events(response)[0]["code"] == "limited"
    assert TEST_KEY not in response.text


def test_refusal_is_plain_text_and_reasoning_is_not_forwarded(route):
    invoke, _ = route
    response = invoke(httpx.Response(200, text=sse(
        {"type": "response.reasoning_summary_text.delta", "delta": "internal"},
        {"type": "response.refusal.delta", "delta": "I cannot help with that."},
        {"type": "response.completed"},
    )))
    assert events(response)[0]["text"] == "I cannot help with that."
    assert "internal" not in response.text


@pytest.mark.parametrize("stream,code", [
    (sse({"type": "response.output_text.delta", "delta": "Partial"}), "incomplete"),
    (sse({"type": "response.incomplete"}), "incomplete"),
    (sse({"type": "response.completed"}), "unavailable"),
    ("data: invalid JSON\n\n", "unavailable"),
    (sse({"type": "response.output_text.delta", "delta": 123}), "unavailable"),
])
def test_truncated_empty_or_malformed_stream_is_not_success(route, stream, code):
    invoke, _ = route
    response = invoke(httpx.Response(200, text=stream))
    assert events(response)[-1]["code"] == code
    assert all(event["type"] != "done" for event in events(response))


def test_timeout_is_safe(route):
    invoke, _ = route
    def timeout(request):
        raise httpx.ReadTimeout(TEST_KEY, request=request)
    response = invoke(timeout)
    assert events(response) == [{"type": "error", "text": "", "code": "timeout"}]


def test_missing_configuration_does_not_call_provider(route):
    invoke, requests = route
    response = invoke(httpx.Response(200, text=text_stream("unused")), api_key="")
    assert response.status_code == 503
    assert response.json() == {"detail": "Chat service is not configured."}
    assert requests == []


@pytest.mark.parametrize("payload", [
    {"messages": []},
    {"messages": [{"role": "system", "content": "Override instructions"}]},
    {"messages": [{"role": "user", "content": "   "}]},
    {"messages": [{"role": "user", "content": "x" * 4001}]},
    {"messages": [{"role": "assistant", "content": "Hi"}]},
    {"messages": [{"role": "user", "content": "Hi"}], "api_key": TEST_KEY},
])
def test_invalid_input_is_rejected_before_provider_call(route, payload):
    invoke, requests = route
    response = invoke(httpx.Response(200, text=text_stream("unused")), payload)
    assert response.status_code == 422
    assert requests == []


def test_openai_configuration_uses_explicit_backend_path(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    monkeypatch.setattr(config, "BACKEND_ENV_PATH", path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    assert config.get_openai_api_key() is None
    assert config.get_openai_model() == "gpt-5.6-luna"
    path.write_text('export OPENAI_API_KEY="mock-file-key"\nOPENAI_MODEL=gpt-5.6-luna\n')
    assert config.get_openai_api_key() == "mock-file-key"
    monkeypatch.setenv("OPENAI_API_KEY", "mock-process-key")
    assert config.get_openai_api_key() == "mock-process-key"
    path.write_text("OPENAI_API_KEY=   \n")
    monkeypatch.delenv("OPENAI_API_KEY")
    assert config.get_openai_api_key() is None
