from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterator


class GenerationFailureCategory(str, Enum):
    """Safe, stable categories for failures in structured generation."""

    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_HTTP_ERROR = "PROVIDER_HTTP_ERROR"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    MALFORMED_JSON = "MALFORMED_JSON"
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
    GROUNDING_VALIDATION_FAILED = "GROUNDING_VALIDATION_FAILED"
    GENERATION_RETRY_EXHAUSTED = "GENERATION_RETRY_EXHAUSTED"
    UNKNOWN_GENERATION_ERROR = "UNKNOWN_GENERATION_ERROR"


@dataclass(frozen=True)
class GenerationContext:
    operation: str
    correlation_id: str
    attempt: int
    provider: Any | None = None
    retry_reason: str | None = None


_generation_context: ContextVar[GenerationContext | None] = ContextVar(
    "career_lens_generation_context",
    default=None,
)

_LOGGER = logging.getLogger("app.llm")
if _LOGGER.level == logging.NOTSET:
    _LOGGER.setLevel(logging.INFO)
if not _LOGGER.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _LOGGER.addHandler(_handler)
_SAFE_FIELD_NAMES = {
    "provider_wait_ms",
    "json_parse_ms",
    "pydantic_validation_ms",
    "grounding_validation_ms",
    "total_attempt_ms",
    "total_operation_ms",
}


def new_correlation_id() -> str:
    """Create a non-sensitive identifier for one generation operation."""

    return uuid.uuid4().hex


@contextmanager
def generation_context(
    *,
    operation: str,
    correlation_id: str,
    attempt: int,
    provider: Any | None = None,
    retry_reason: str | None = None,
) -> Iterator[None]:
    """Make safe operation metadata available to provider-level logging."""

    token = _generation_context.set(
        GenerationContext(
            operation=operation,
            correlation_id=correlation_id,
            attempt=attempt,
            provider=provider,
            retry_reason=retry_reason,
        )
    )
    try:
        yield
    finally:
        _generation_context.reset(token)


def current_generation_context() -> GenerationContext | None:
    return _generation_context.get()


def elapsed_ms(started_at: float) -> float:
    """Return a rounded monotonic duration suitable for logs."""

    return round((time.perf_counter() - started_at) * 1000, 2)


def provider_metadata(provider: Any | None) -> dict[str, Any]:
    """Return only non-sensitive provider configuration metadata."""

    if provider is None:
        return {}
    metadata: dict[str, Any] = {
        "provider_name": type(provider).__name__,
    }
    for key, output_key in (
        ("model", "model_name"),
        ("num_ctx", "context_length"),
        ("timeout_seconds", "configured_timeout_seconds"),
    ):
        value = getattr(provider, key, None)
        if isinstance(value, (str, int, float)):
            metadata[output_key] = value
    return metadata


def provider_status_code(error: BaseException) -> int | None:
    value = getattr(error, "status_code", None)
    return value if isinstance(value, int) else None


def classify_generation_error(error: BaseException) -> GenerationFailureCategory:
    """Classify known provider and structured-output errors without messages."""

    category = getattr(error, "failure_category", None)
    if isinstance(category, GenerationFailureCategory):
        return category
    if isinstance(category, str):
        try:
            return GenerationFailureCategory(category)
        except ValueError:
            pass

    name = type(error).__name__
    if name == "OllamaProviderUnavailableError":
        return GenerationFailureCategory.PROVIDER_UNAVAILABLE
    if name == "OllamaTimeoutError":
        return GenerationFailureCategory.PROVIDER_TIMEOUT
    if name == "OllamaProviderError":
        return GenerationFailureCategory.PROVIDER_HTTP_ERROR
    if name == "StructuredOutputError":
        return GenerationFailureCategory.MALFORMED_JSON
    if name == "ValidationError":
        return GenerationFailureCategory.SCHEMA_VALIDATION_FAILED
    return GenerationFailureCategory.UNKNOWN_GENERATION_ERROR


def log_generation_event(
    *,
    event: str,
    success: bool,
    provider: Any | None = None,
    operation: str | None = None,
    correlation_id: str | None = None,
    attempt: int | None = None,
    retry_reason: str | None = None,
    failure_category: GenerationFailureCategory | str | None = None,
    root_failure_category: GenerationFailureCategory | str | None = None,
    provider_http_status: int | None = None,
    **fields: Any,
) -> None:
    """Emit a bounded JSON log record with no prompt, answer, or model text."""

    context = current_generation_context()
    active_provider = provider or (context.provider if context else None)
    payload: dict[str, Any] = {
        "event": event,
        "success": success,
        "operation": operation or (context.operation if context else "unknown"),
        "correlation_id": correlation_id
        or (context.correlation_id if context else "unknown"),
        "attempt": attempt if attempt is not None else (context.attempt if context else None),
        **provider_metadata(active_provider),
    }
    active_retry_reason = retry_reason or (
        context.retry_reason if context else None
    )
    if active_retry_reason:
        payload["retry_reason"] = active_retry_reason
    if failure_category is not None:
        payload["failure_category"] = (
            failure_category.value
            if isinstance(failure_category, GenerationFailureCategory)
            else str(failure_category)
        )
    if root_failure_category is not None:
        payload["root_failure_category"] = (
            root_failure_category.value
            if isinstance(root_failure_category, GenerationFailureCategory)
            else str(root_failure_category)
        )
    if provider_http_status is not None:
        payload["provider_http_status"] = provider_http_status

    # Callers can provide timing and retry fields, but values are restricted to
    # scalar data so prompts, responses, and credentials cannot be logged.
    for key, value in fields.items():
        if key not in _SAFE_FIELD_NAMES:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            payload[key] = value

    _LOGGER.info(json.dumps(payload, sort_keys=True, separators=(",", ":")))
