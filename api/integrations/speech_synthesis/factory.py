"""Factory: picks the active SpeechSynthesizer from config."""
from functools import lru_cache

from api.config import settings
from api.integrations.speech_synthesis.base import SpeechSynthesizer
from api.integrations.speech_synthesis.mock_adapter import MockSpeechSynthesizer


@lru_cache
def get_speech_synthesizer() -> SpeechSynthesizer:
    if settings.OPENAI_API_KEY:
        from api.integrations.speech_synthesis.openai_adapter import OpenAISpeechSynthesizer

        return OpenAISpeechSynthesizer()
    return MockSpeechSynthesizer()
