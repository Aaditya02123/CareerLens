from __future__ import annotations

import json
import os
from urllib import error, request
from typing import Any

from app.services.llm.generator import LLMGenerationProvider


class OllamaConfigurationError(RuntimeError):
    """Raised when Ollama configuration is invalid."""


class OllamaProviderError(RuntimeError):
    """Raised when Ollama returns an unusable response."""


class OllamaProviderUnavailableError(OllamaProviderError):
    """Raised when the Ollama service cannot be reached."""


class OllamaTimeoutError(OllamaProviderError):
    """Raised when an Ollama request exceeds its timeout."""


class OllamaGenerationProvider:
    """Generate text using a locally running Ollama model."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 300.0,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL")
            or "http://127.0.0.1:11434"
        ).rstrip("/")

        self.model = (
            model
            or os.getenv("OLLAMA_MODEL")
            or "qwen3.5:9b"
        )

        self.timeout_seconds = timeout_seconds

    def _request(
        self,
        *,
        system_prompt: str,
        prompt: str,
        response_format: str | dict[str, Any] | None = None,
    ) -> str:
        if not self.model.strip():
            raise OllamaConfigurationError(
                "OLLAMA_MODEL must not be empty."
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "stream": False,
            "options": {
                "temperature": 0,
            },
        }
        if response_format is not None:
            payload["format"] = response_format

        data = json.dumps(payload).encode("utf-8")

        http_request = request.Request(
            url=f"{self.base_url}/api/chat",
            data=data,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(
                http_request,
                timeout=self.timeout_seconds,
            ) as response:
                response_body = response.read().decode("utf-8")

        except error.HTTPError as exc:
            raise OllamaProviderError(
                f"Ollama returned HTTP {exc.code}."
            ) from exc

        except error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise OllamaTimeoutError(
                    "The Ollama request timed out."
                ) from exc
            raise OllamaProviderUnavailableError(
                "Could not connect to Ollama. "
                "Make sure the Ollama service is running."
            ) from exc

        except TimeoutError as exc:
            raise OllamaTimeoutError("The Ollama request timed out.") from exc

        try:
            result = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise OllamaProviderError(
                "Ollama returned invalid JSON."
            ) from exc

        content = (
            result.get("message", {})
            .get("content", "")
        )

        if not isinstance(content, str) or not content.strip():
            raise OllamaProviderError(
                "Ollama response did not contain generated text."
            )

        return content.strip()

    def generate(
        self,
        system_prompt: str,
        prompt: str,
    ) -> str:
        """Generate unconstrained text using Ollama."""
        return self._request(system_prompt=system_prompt, prompt=prompt)

    def generate_structured(
        self,
        *,
        system_prompt: str,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> str:
        """Generate JSON constrained by Ollama's native schema support."""
        return self._request(
            system_prompt=system_prompt,
            prompt=prompt,
            response_format=response_schema,
        )


def get_ollama_generation_provider() -> LLMGenerationProvider:
    """Create the configured Ollama generation provider."""

    return OllamaGenerationProvider()
