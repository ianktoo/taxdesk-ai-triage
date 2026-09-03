"""Factory: picks the active Reasoner from config.

Mirrors the other capability factories: business logic asks for a
Reasoner, never for a specific vendor. With no OPENAI_API_KEY the
deterministic mock keeps the whole agent pipeline running.
"""
from functools import lru_cache

from api.config import settings
from api.integrations.reasoning.base import Reasoner
from api.integrations.reasoning.mock_adapter import MockReasoner


@lru_cache
def get_reasoner() -> Reasoner:
    if settings.OPENAI_API_KEY and settings.AGENT_REASONER != "mock":
        from api.integrations.reasoning.openai_adapter import OpenAIReasoner

        return OpenAIReasoner()
    return MockReasoner()


@lru_cache
def get_fallback_reasoner() -> Reasoner:
    """The deterministic reasoner, regardless of config.

    The orchestrator falls back to this for a single agent whose model
    call failed, so one flaky inference degrades that step's quality
    instead of failing the whole request.
    """
    return MockReasoner()
