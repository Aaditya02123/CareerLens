from app.services.llm.ollama_generator import (
    OllamaGenerationProvider,
)


def test_ollama_provider_uses_configured_model():
    provider = OllamaGenerationProvider(
        base_url="http://127.0.0.1:11434",
        model="qwen3.5:9b",
    )

    assert provider.model == "qwen3.5:9b"
    assert provider.base_url == "http://127.0.0.1:11434"


def test_ollama_provider_can_be_typed_as_generation_provider():
    provider = OllamaGenerationProvider(
        model="qwen3.5:9b",
    )

    assert hasattr(provider, "generate")