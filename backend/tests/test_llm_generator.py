from app.services.llm.generator import LLMGenerationProvider


class FakeGenerationProvider:
    def __init__(self, response: str):
        self.response = response
        self.system_prompt = None
        self.prompt = None
        self.call_count = 0

    def generate(
        self,
        system_prompt: str,
        prompt: str,
    ) -> str:
        self.call_count += 1
        self.system_prompt = system_prompt
        self.prompt = prompt
        return self.response


def test_fake_generation_provider_returns_text():
    provider = FakeGenerationProvider(
        response="Your strongest alignment is backend development."
    )

    result = provider.generate(
        system_prompt="You are a career intelligence assistant.",
        prompt="Explain this job match.",
    )

    assert result == "Your strongest alignment is backend development."


def test_fake_generation_provider_receives_prompts():
    provider = FakeGenerationProvider(
        response="Grounded explanation."
    )

    provider.generate(
        system_prompt="System instructions",
        prompt="Explain the evidence.",
    )

    assert provider.call_count == 1
    assert provider.system_prompt == "System instructions"
    assert provider.prompt == "Explain the evidence."


def test_fake_generation_provider_satisfies_generation_contract():
    provider = FakeGenerationProvider(
        response="Test response."
    )

    generation_provider: LLMGenerationProvider = provider

    result = generation_provider.generate(
        system_prompt="System",
        prompt="Prompt",
    )

    assert result == "Test response."