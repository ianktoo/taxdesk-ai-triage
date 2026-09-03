"""Mock TextGenerator, deterministic canned output, no network calls."""
from api.integrations.text_generation.base import GeneratedPersonaText

_MOCK_NAMES = ["Alex Rivera", "Priya Nandakumar", "Tomas Berg", "Keisha Monroe"]


class MockTextGenerator:
    def generate_persona(self, scenario: str) -> GeneratedPersonaText:
        # Deterministic-ish pick so repeated demo calls don't feel random.
        name = _MOCK_NAMES[len(scenario) % len(_MOCK_NAMES)]
        return GeneratedPersonaText(
            display_name=name,
            message=(
                f"Hi, I'm reaching out about the following: {scenario.strip()} "
                "I've attached what I think is relevant, let me know if you need "
                "anything else from me."
            ),
        )
