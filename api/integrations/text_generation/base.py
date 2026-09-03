"""Contract for the TextGenerator capability.

Anything that can turn a short scenario prompt into structured text
(OpenAI, another LLM vendor, or a mock) implements this Protocol.
Services must only ever depend on this interface.
"""
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class GeneratedPersonaText:
    display_name: str
    message: str


class TextGenerationError(Exception):
    """Normalized error for the TextGenerator capability."""


@runtime_checkable
class TextGenerator(Protocol):
    def generate_persona(self, scenario: str) -> GeneratedPersonaText:
        """Turns a short scenario description into a customer name + message."""
        ...
