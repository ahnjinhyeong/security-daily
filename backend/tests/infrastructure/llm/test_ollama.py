import json

import httpx
import pytest

from security_daily.infrastructure.llm.errors import (
    LLMConnectionError,
    LLMResponseError,
)
from security_daily.infrastructure.llm.ollama import OllamaLLMProvider


def test_ollama_provider_sends_schema_and_validates_envelope() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["model"] == "phi4-mini"
        assert body["stream"] is False
        assert body["think"] is False
        assert body["format"] == {"type": "object"}
        assert body["options"] == {"temperature": 0, "num_predict": 1024}
        return httpx.Response(
            200,
            json={"message": {"content": '{"selections": []}'}},
        )

    client = httpx.Client(
        base_url="http://ollama.test", transport=httpx.MockTransport(handler)
    )
    provider = OllamaLLMProvider("http://ignored", 1, client)

    result = provider.generate_json(
        model="phi4-mini",
        system_prompt="system",
        user_prompt="user",
        schema={"type": "object"},
        max_output_tokens=1024,
    )

    assert result == {"selections": []}


def test_ollama_provider_rejects_invalid_response() -> None:
    client = httpx.Client(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"message": {"content": "no"}})
        ),
    )
    provider = OllamaLLMProvider("http://ignored", 1, client)

    with pytest.raises(LLMResponseError):
        provider.generate_json(
            model="model", system_prompt="s", user_prompt="u", schema={}
        )


def test_ollama_provider_reports_http_error_without_response_body() -> None:
    client = httpx.Client(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(500, text="secret response")
        ),
    )
    provider = OllamaLLMProvider("http://ignored", 1, client)

    with pytest.raises(LLMConnectionError, match="HTTP 500") as error:
        provider.generate_json(
            model="model", system_prompt="s", user_prompt="u", schema={}
        )
    assert "secret response" not in str(error.value)
