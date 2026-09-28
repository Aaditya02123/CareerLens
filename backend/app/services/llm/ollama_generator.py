from __future__ import annotations

import json
import os
from urllib import error, request

from app.services.llm.generator import LLMGenerationProvider


class OllamaConfigurationError(RuntimeError):
    """Raised when Ollama configuration is invalid."""


class OllamaProviderError(RuntimeError):
    """Raised when Ollama returns an unusable response."""


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

    def generate(
        self,
        system_prompt: str,
        prompt: str,
    ) -> str:
        if not self.model.strip():
            raise OllamaConfigurationError(
                "OLLAMA_MODEL must not be empty."
            )

        payload = {
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
            body = exc.read().decode("utf-8", errors="replace")
            raise OllamaProviderError(
                f"Ollama returned HTTP {exc.code}: {body}"
            ) from exc

        except error.URLError as exc:
            raise OllamaProviderError(
                "Could not connect to Ollama. "
                "Make sure the Ollama service is running."
            ) from exc

        except TimeoutError as exc:
            raise OllamaProviderError(
                "Ollama request timed out."
            ) from exc

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


def get_ollama_generation_provider() -> LLMGenerationProvider:
    """Create the configured Ollama generation provider."""

    return OllamaGenerationProvider()