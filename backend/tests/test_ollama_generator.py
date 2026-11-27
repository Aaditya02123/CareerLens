import json
from urllib.error import URLError

import pytest

from app.services.llm.ollama_generator import (
    OllamaGenerationProvider,
    OllamaProviderError,
    OllamaProviderUnavailableError,
    OllamaTimeoutError,
)


def test_ollama_provider_uses_configured_model():
    provider = OllamaGenerationProvider(
        base_url="http://127.0.0.1:11434",
        model="qwen3.5:4b",
    )

    assert provider.model == "qwen3.5:4b"
    assert provider.base_url == "http://127.0.0.1:11434"


def test_ollama_provider_reads_model_and_context_from_environment(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:4b")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "8192")

    provider = OllamaGenerationProvider()

    assert provider.model == "qwen3.5:4b"
    assert provider.num_ctx == 8192


def test_ollama_provider_can_be_typed_as_generation_provider():
    provider = OllamaGenerationProvider(
        model="qwen3.5:4b",
    )

    assert hasattr(provider, "generate")


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_structured_generation_sends_native_json_schema(monkeypatch):
    captured = {}

    def fake_urlopen(http_request, timeout):
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response({"message": {"content": '{"ok": true}'}})

    monkeypatch.setattr(
        "app.services.llm.ollama_generator.request.urlopen",
        fake_urlopen,
    )
    provider = OllamaGenerationProvider(timeout_seconds=17)
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}

    result = provider.generate_structured(
        system_prompt="system",
        prompt="prompt",
        response_schema=schema,
    )

    assert result == '{"ok": true}'
    assert captured["body"]["format"] == schema
    assert captured["body"]["options"]["temperature"] == 0
    assert captured["body"]["options"]["num_ctx"] == 8192
    assert captured["timeout"] == 17


def test_provider_unavailable_error_is_classified(monkeypatch):
    def raise_unavailable(*args, **kwargs):
        raise URLError("offline")

    monkeypatch.setattr(
        "app.services.llm.ollama_generator.request.urlopen",
        raise_unavailable,
    )

    with pytest.raises(OllamaProviderUnavailableError):
        OllamaGenerationProvider().generate("system", "prompt")


def test_provider_timeout_is_classified(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise TimeoutError()

    monkeypatch.setattr(
        "app.services.llm.ollama_generator.request.urlopen",
        raise_timeout,
    )

    with pytest.raises(OllamaTimeoutError):
        OllamaGenerationProvider().generate("system", "prompt")


def test_provider_invalid_response_envelope_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "app.services.llm.ollama_generator.request.urlopen",
        lambda *args, **kwargs: _Response({"message": {"content": ""}}),
    )

    with pytest.raises(OllamaProviderError):
        OllamaGenerationProvider().generate("system", "prompt")
