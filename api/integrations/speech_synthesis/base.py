"""Contract for the SpeechSynthesizer capability.

Anything that can turn text into spoken audio implements this
Protocol. Services must only ever depend on this interface.
"""
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class SynthesizedSpeech:
    audio_bytes: bytes
    content_type: str  # e.g. "audio/mpeg"


class SpeechSynthesisError(Exception):
    """Normalized error for the SpeechSynthesizer capability."""


@runtime_checkable
class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str) -> SynthesizedSpeech:
        """Turns text into spoken audio."""
        ...
