import json
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from security_daily.infrastructure.llm.errors import (
    LLMConnectionError,
    LLMResponseError,
)


class _OllamaMessage(BaseModel):
    content: str


class _OllamaChatResponse(BaseModel):
    message: _OllamaMessage


class OllamaLLMProvider:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        client: httpx.Client | None = None,
    ) -> None:
        self._client = client or httpx.Client(
            base_url=base_url.rstrip("/"), timeout=timeout_seconds
        )
        self._owns_client = client is None

    def generate_json(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        options: dict[str, int | float] = {"temperature": 0}
        if max_output_tokens is not None:
            options["num_predict"] = max_output_tokens
        try:
            response = self._client.post(
                "/api/chat",
                json={
                    "model": model,
                    "stream": False,
                    "think": False,
                    "format": schema,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "options": options,
                },
            )
            response.raise_for_status()
        except (httpx.TimeoutException, httpx.TransportError) as error:
            raise LLMConnectionError("Ollama API connection failed") from error
        except httpx.HTTPStatusError as error:
            raise LLMConnectionError(
                f"Ollama API returned HTTP {error.response.status_code}"
            ) from error

        try:
            envelope = _OllamaChatResponse.model_validate(response.json())
            payload = json.loads(envelope.message.content)
        except (ValueError, ValidationError, json.JSONDecodeError) as error:
            raise LLMResponseError("Ollama returned an invalid JSON response") from error
        if not isinstance(payload, dict):
            raise LLMResponseError("Ollama structured response must be a JSON object")
        return payload

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "OllamaLLMProvider":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
