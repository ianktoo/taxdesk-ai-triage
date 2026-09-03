"""Factory: picks the active TextGenerator from config."""
from functools import lru_cache

from api.config import settings
from api.integrations.text_generation.base import TextGenerator
from api.integrations.text_generation.mock_adapter import MockTextGenerator


@lru_cache
def get_text_generator() -> TextGenerator:
    if settings.OPENAI_API_KEY:
        from api.integrations.text_generation.openai_adapter import OpenAITextGenerator

        return OpenAITextGenerator()
    return MockTextGenerator()
