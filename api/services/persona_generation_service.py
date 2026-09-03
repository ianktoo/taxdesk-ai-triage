"""Business logic: turning an agent-written scenario into a draft persona.

Talks to the TextGeneration capability only through its contract
(api.integrations.text_generation.base). No vendor SDK imports here.
"""
from dataclasses import dataclass

from api.integrations.text_generation.base import TextGenerator


@dataclass
class DraftPersona:
    display_name: str
    message: str


MAX_SCENARIO_LENGTH = 400


def generate_draft_persona(scenario: str, generator: TextGenerator) -> DraftPersona:
    scenario = scenario.strip()
    if not scenario:
        raise ValueError("Scenario cannot be empty")
    if len(scenario) > MAX_SCENARIO_LENGTH:
        scenario = scenario[:MAX_SCENARIO_LENGTH]

    generated = generator.generate_persona(scenario)
    return DraftPersona(display_name=generated.display_name, message=generated.message)
