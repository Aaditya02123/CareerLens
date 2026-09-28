from __future__ import annotations

from typing import Protocol


class LLMGenerationProvider(Protocol):
    """Provider abstraction for generic LLM text generation."""

    def generate(
        self,
        system_prompt: str,
        prompt: str,
    ) -> str:
        ...