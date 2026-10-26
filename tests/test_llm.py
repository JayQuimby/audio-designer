import json

import httpx
import pytest

from voice_assist.llm import LLMError, Message, ProviderConfig, make_provider

MSGS = [Message("user", "hi")]


def provider(kind, handler, **cfg):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return make_provider(ProviderConfig(provider=kind, model="m", api_key="k", **cfg), client)


def sse(*events):
    return "".join(f"data: {json.dumps(e)}\n\n" for e in events) + "data: [DONE]\n\n"


def test_no_provider_configured():
    assert make_provider(ProviderConfig()) is None


def test_unknown_provider():
    with pytest.raises(LLMError):
        make_provider(ProviderConfig(provider="nope"))


def test_openai_streams_and_sends_low_effort():
    seen = []

    def handler(req):
        body = json.loads(req.content)
        seen.append(body)
        assert req.headers["authorization"] == "Bearer k"
        assert body["messages"][0] == {"role": "system", "content": "sys"}
        return httpx.Response(200, text=sse(
            {"choices": [{"delta": {"role": "assistant"}}]},
            {"choices": [{"delta": {"content": "Hel"}}]},
            {"choices": [{"delta": {"content": "lo"}}]},
        ))

    assert provider("openai", handler).complete(MSGS, "sys") == "Hello"
    assert seen[0]["reasoning_effort"] == "low"


def test_openai_retries_without_reasoning_effort_on_400():
    bodies = []

    def handler(req):
        body = json.loads(req.content)
        bodies.append(body)
        if "reasoning_effort" in body:
            return httpx.Response(400, json={"error": {"message": "unsupported parameter"}})
        return httpx.Response(200, text=sse({"choices": [{"delta": {"content": "ok"}}]}))

    assert provider("openai", handler).complete(MSGS, "s") == "ok"
    assert len(bodies) == 2 and "reasoning_effort" not in bodies[1]


def test_anthropic_streams_text_deltas():
    def handler(req):
        assert req.headers["x-api-key"] == "k" and req.headers["anthropic-version"]
        body = json.loads(req.content)
        assert body["system"] == "sys" and "thinking" not in body and body["max_tokens"]
        return httpx.Response(200, text=sse(
            {"type": "message_start"},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hi "}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "there"}},
            {"type": "message_stop"},
        ))

    assert provider("anthropic", handler).complete(MSGS, "sys") == "Hi there"


def test_ollama_streams_ndjson_and_lists_models():
    def handler(req):
        if req.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "b"}, {"name": "a"}]})
        lines = [{"message": {"content": "He"}}, {"message": {"content": "y"}}, {"done": True}]
        return httpx.Response(200, text="\n".join(json.dumps(x) for x in lines))

    p = provider("ollama", handler)
    assert p.complete(MSGS, "s") == "Hey"
    assert p.list_models() == ["a", "b"]
    assert p.base_url == "http://localhost:11434"


def test_auth_error_is_readable():
    def handler(req):
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    with pytest.raises(LLMError, match="check your API key"):
        provider("openai", handler).complete(MSGS, "s")


def test_unreachable_server_is_readable():
    def handler(req):
        raise httpx.ConnectError("refused")

    with pytest.raises(LLMError, match="not reachable"):
        provider("ollama", handler).complete(MSGS, "s")
