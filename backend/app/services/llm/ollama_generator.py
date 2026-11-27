from __future__ import annotations

import json
import os
import time
from threading import Lock
from urllib import error, request
from typing import Any

from app.services.llm.generator import LLMGenerationProvider
from app.services.llm.observability import (
    GenerationFailureCategory,
    classify_generation_error,
    elapsed_ms,
    log_generation_event,
)


class OllamaConfigurationError(RuntimeError):
    """Raised when Ollama configuration is invalid."""


class OllamaProviderError(RuntimeError):
    """Raised when Ollama returns an unusable response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class OllamaProviderUnavailableError(OllamaProviderError):
    """Raised when the Ollama service cannot be reached."""

    failure_category = GenerationFailureCategory.PROVIDER_UNAVAILABLE


class OllamaTimeoutError(OllamaProviderError):
    """Raised when an Ollama request exceeds its timeout."""

    failure_category = GenerationFailureCategory.PROVIDER_TIMEOUT


_GENERATION_LOCK = Lock()


def _positive_int_from_environment(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise OllamaConfigurationError(
            f"{name} must be a positive integer."
        ) from exc

    if value <= 0:
        raise OllamaConfigurationError(
            f"{name} must be a positive integer."
        )
    return value


class OllamaGenerationProvider:
    """Generate text using a locally running Ollama model."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 300.0,
        num_ctx: int | None = None,
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
        if num_ctx is None:
            self.num_ctx = _positive_int_from_environment(
                "OLLAMA_NUM_CTX",
                8192,
            )
        elif num_ctx <= 0:
            raise OllamaConfigurationError(
                "num_ctx must be a positive integer."
            )
        else:
            self.num_ctx = num_ctx

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
                "num_ctx": self.num_ctx,
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

        provider_started_at = time.perf_counter()
        try:
            # Ollama's OLLAMA_NUM_PARALLEL is a server setting. This lock also
            # keeps one backend process from issuing concurrent generations.
            with _GENERATION_LOCK:
                with request.urlopen(
                    http_request,
                    timeout=self.timeout_seconds,
                ) as response:
                    response_body = response.read().decode("utf-8")

        except error.HTTPError as exc:
            provider_error = OllamaProviderError(
                f"Ollama returned HTTP {exc.code}.",
                status_code=exc.code,
            )
            log_generation_event(
                event="llm_provider_request",
                success=False,
                provider=self,
                failure_category=classify_generation_error(provider_error),
                provider_http_status=provider_error.status_code,
                provider_wait_ms=elapsed_ms(provider_started_at),
            )
            raise provider_error from exc

        except error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                provider_error = OllamaTimeoutError(
                    "The Ollama request timed out."
                )
            else:
                provider_error = OllamaProviderUnavailableError(
                    "Could not connect to Ollama. "
                    "Make sure the Ollama service is running."
                )
            log_generation_event(
                event="llm_provider_request",
                success=False,
                provider=self,
                failure_category=classify_generation_error(provider_error),
                provider_wait_ms=elapsed_ms(provider_started_at),
            )
            raise provider_error from exc

        except TimeoutError as exc:
            provider_error = OllamaTimeoutError("The Ollama request timed out.")
            log_generation_event(
                event="llm_provider_request",
                success=False,
                provider=self,
                failure_category=classify_generation_error(provider_error),
                provider_wait_ms=elapsed_ms(provider_started_at),
            )
            raise provider_error from exc

        try:
            result = json.loads(response_body)
        except json.JSONDecodeError as exc:
            provider_error = OllamaProviderError("Ollama returned invalid JSON.")
            log_generation_event(
                event="llm_provider_request",
                success=False,
                provider=self,
                failure_category=GenerationFailureCategory.MALFORMED_JSON,
                provider_wait_ms=elapsed_ms(provider_started_at),
            )
            raise provider_error from exc

        content = (
            result.get("message", {})
            .get("content", "")
        )

        if not isinstance(content, str) or not content.strip():
            provider_error = OllamaProviderError(
                "Ollama response did not contain generated text."
            )
            log_generation_event(
                event="llm_provider_request",
                success=False,
                provider=self,
                failure_category=GenerationFailureCategory.UNKNOWN_GENERATION_ERROR,
                provider_wait_ms=elapsed_ms(provider_started_at),
            )
            raise provider_error

        log_generation_event(
            event="llm_provider_request",
            success=True,
            provider=self,
            provider_wait_ms=elapsed_ms(provider_started_at),
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
