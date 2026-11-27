import json
import logging

from app.models.interview_blueprint import InterviewBlueprintConfig
from app.services.llm.observability import (
    GenerationFailureCategory,
    classify_generation_error,
    generation_context,
    log_generation_event,
)
from app.services.llm.ollama_generator import (
    OllamaProviderError,
    OllamaProviderUnavailableError,
    OllamaTimeoutError,
)
from app.services.llm.structured import parse_and_validate_model


def test_failure_categories_cover_provider_and_structured_stages():
    assert (
        classify_generation_error(OllamaProviderUnavailableError("offline"))
        == GenerationFailureCategory.PROVIDER_UNAVAILABLE
    )
    assert (
        classify_generation_error(OllamaTimeoutError("timeout"))
        == GenerationFailureCategory.PROVIDER_TIMEOUT
    )
    assert (
        classify_generation_error(OllamaProviderError("HTTP 500", status_code=500))
        == GenerationFailureCategory.PROVIDER_HTTP_ERROR
    )


def test_structured_validation_reports_parse_and_pydantic_timings():
    result = parse_and_validate_model(
        '{"question_count": 1, "interview_type": "technical", '
        '"duration_minutes": 5, "difficulty": "easy", '
        '"focus_competencies": []}',
        InterviewBlueprintConfig,
    )

    assert result.value.question_count == 1
    assert result.json_parse_ms >= 0
    assert result.pydantic_validation_ms >= 0


def test_observability_log_is_json_and_contains_no_prompt_content(caplog):
    caplog.set_level(logging.INFO, logger="app.llm")
    secret_prompt_fragment = "candidate resume private text"

    with generation_context(
        operation="blueprint",
        correlation_id="correlation-1",
        attempt=1,
    ):
        log_generation_event(
            event="llm_generation",
            success=False,
            failure_category=GenerationFailureCategory.MALFORMED_JSON,
            retry_reason="invalid response",
            prompt=secret_prompt_fragment,
        )

    payload = json.loads(caplog.records[-1].message)
    assert payload["operation"] == "blueprint"
    assert payload["correlation_id"] == "correlation-1"
    assert payload["failure_category"] == "MALFORMED_JSON"
    assert secret_prompt_fragment not in caplog.text
    assert "prompt" not in payload
