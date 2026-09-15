from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request

from app.services.llm.base import LLMEvaluationPayload


class LLMConfigurationError(RuntimeError):
    """Raised when LLM configuration is missing."""


class LLMProviderError(RuntimeError):
    """Raised when the provider returns an unusable response."""


class OpenAICompatibleInterviewProvider:
    """OpenAI-compatible provider implemented with the standard library."""

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.api_url = api_url or os.getenv(
            "LLM_API_URL",
            "https://api.openai.com/v1/chat/completions",
        )
        self.model = model or os.getenv(
            "LLM_MODEL",
            "gpt-4o-mini",
        )
        self.timeout_seconds = timeout_seconds

    def evaluate(
        self,
        prompt: str,
        context: dict[str, Any],
    ) -> LLMEvaluationPayload:
        """Call the provider and validate its JSON response."""
        if not self.api_key:
            raise LLMConfigurationError(
                "LLM_API_KEY is required for LLM evaluation."
            )

        payload = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a careful interview-answer evaluator. "
                        "Return only the requested JSON object."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

        http_request = request.Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(
                http_request,
                timeout=self.timeout_seconds,
            ) as response:
                response_data = json.loads(
                    response.read().decode("utf-8")
                )
        except (error.URLError, error.HTTPError, TimeoutError) as exc:
            raise LLMProviderError(
                "The configured LLM provider could not be reached."
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LLMProviderError(
                "The LLM provider returned an invalid response."
            ) from exc

        try:
            content = response_data["choices"][0]["message"]["content"]

            if isinstance(content, list):
                content = "".join(
                    part.get("text", "")
                    for part in content
                    if isinstance(part, dict)
                )

            if not isinstance(content, str):
                raise TypeError("Provider content was not text.")

            cleaned_content = content.strip()

            if cleaned_content.startswith("```"):
                cleaned_content = (
                    cleaned_content.removeprefix("```json")
                    .removeprefix("```")
                    .removesuffix("```")
                    .strip()
                )

            return LLMEvaluationPayload.model_validate_json(
                cleaned_content
            )
        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise LLMProviderError(
                "The LLM provider returned an invalid evaluation payload."
            ) from exc