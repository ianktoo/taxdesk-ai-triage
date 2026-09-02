"""Factory: picks the active DocumentExtractor from config.

Business logic must call get_document_extractor() and never
import a specific adapter directly.
"""
from functools import lru_cache

from api.config import settings
from api.integrations.document_extraction.base import DocumentExtractor
from api.integrations.document_extraction.mock_adapter import MockDocumentExtractor


@lru_cache
def get_document_extractor() -> DocumentExtractor:
    if settings.DOCUMENT_EXTRACTOR == "mock":
        return MockDocumentExtractor()
    if settings.DOCUMENT_EXTRACTOR == "nutrient":
        from api.integrations.document_extraction.nutrient_adapter import (
            NutrientDocumentExtractor,
        )

        return NutrientDocumentExtractor()
    raise ValueError(f"Unknown DOCUMENT_EXTRACTOR: {settings.DOCUMENT_EXTRACTOR!r}")
