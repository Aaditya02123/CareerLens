import pytest

from app.services.llm.structured import (
    StructuredOutputError,
    generate_structured_text,
    parse_json_object,
)


def test_parse_json_object_accepts_whitespace_and_json_code_fence():
    assert parse_json_object('  {"value": 1}  ') == {"value": 1}
    assert parse_json_object('```json\n{"value": 1}\n```') == {"value": 1}


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        '{"first": 1} {"second": 2}',
        "```json\n{\"value\": 1}\n``` trailing text",
        "[1, 2, 3]",
    ],
)
def test_parse_json_object_rejects_ambiguous_or_invalid_output(raw):
    with pytest.raises(StructuredOutputError):
        parse_json_object(raw)


def test_generate_structured_text_uses_native_provider_method():
    class StructuredProvider:
        def generate_structured(self, **kwargs):
            self.kwargs = kwargs
            return '{"ok": true}'

    provider = StructuredProvider()
    result = generate_structured_text(
        provider,
        system_prompt="system",
        prompt="prompt",
        response_schema={"type": "object"},
    )

    assert result == '{"ok": true}'
    assert provider.kwargs["response_schema"] == {"type": "object"}


def test_generate_structured_text_keeps_legacy_provider_compatibility():
    class LegacyProvider:
        def generate(self, *, system_prompt, prompt):
            self.prompts = system_prompt, prompt
            return '{"ok": true}'

    provider = LegacyProvider()
    result = generate_structured_text(
        provider,
        system_prompt="system",
        prompt="prompt",
        response_schema={"type": "object"},
    )

    assert result == '{"ok": true}'
    assert provider.prompts == ("system", "prompt")
