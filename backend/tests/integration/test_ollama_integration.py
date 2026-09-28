import os

import pytest

from app.services.llm.ollama_generator import OllamaGenerationProvider


@pytest.mark.integration
def test_ollama_qwen_generation():
    if os.getenv("RUN_OLLAMA_INTEGRATION") != "1":
        pytest.skip("Set RUN_OLLAMA_INTEGRATION=1 to run Ollama integration tests.")

    provider = OllamaGenerationProvider(
        model=os.getenv("OLLAMA_MODEL", "qwen3.5:9b"),
    )

    result = provider.generate(
        system_prompt=(
            "You are a concise career intelligence assistant. "
            "Return only a short plain-text answer."
        ),
        prompt=(
            "In one sentence, explain why Python is useful "
            "for backend development."
        ),
    )

    assert isinstance(result, str)
    assert result.strip()