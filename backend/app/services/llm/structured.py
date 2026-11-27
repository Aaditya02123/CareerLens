from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any


class StructuredOutputError(ValueError):
    """Raised when a provider response is not one JSON object."""


@dataclass(frozen=True)
class StructuredValidationResult:
    """Validated model plus parsing and Pydantic validation durations."""

    value: Any
    json_parse_ms: float
    pydantic_validation_ms: float


def parse_json_object(raw: Any) -> dict[str, Any]:
    """Parse one JSON object, allowing only an unambiguous code fence."""
    if isinstance(raw, dict):
        value = raw
    elif isinstance(raw, str):
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            match = re.fullmatch(
                r"```(?:json)?\s*(.*?)\s*```",
                cleaned,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if match is None:
                raise StructuredOutputError(
                    "Structured output contained an ambiguous code fence."
                )
            cleaned = match.group(1).strip()

        try:
            value = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError) as error:
            raise StructuredOutputError(
                "Structured output was not valid JSON."
            ) from error
    else:
        raise StructuredOutputError(
            "Structured output must be a JSON object or JSON text."
        )

    if not isinstance(value, dict):
        raise StructuredOutputError(
            "Structured output must contain exactly one JSON object."
        )
    return value


def parse_and_validate_model(raw: Any, model_type: Any) -> StructuredValidationResult:
    """Parse one JSON object and validate it with the supplied Pydantic model."""

    parse_started_at = time.perf_counter()
    parsed = parse_json_object(raw)
    json_parse_ms = round((time.perf_counter() - parse_started_at) * 1000, 2)

    validation_started_at = time.perf_counter()
    value = model_type.model_validate(parsed)
    pydantic_validation_ms = round(
        (time.perf_counter() - validation_started_at) * 1000,
        2,
    )
    return StructuredValidationResult(
        value=value,
        json_parse_ms=json_parse_ms,
        pydantic_validation_ms=pydantic_validation_ms,
    )


def generate_structured_text(
    provider: Any,
    *,
    system_prompt: str,
    prompt: str,
    response_schema: dict[str, Any],
) -> str:
    """Use native structured generation when the provider supports it."""
    structured_generate = getattr(provider, "generate_structured", None)
    if callable(structured_generate):
        return structured_generate(
            system_prompt=system_prompt,
            prompt=prompt,
            response_schema=response_schema,
        )
    return provider.generate(system_prompt=system_prompt, prompt=prompt)
