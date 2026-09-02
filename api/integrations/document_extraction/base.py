"""Contract for the DocumentExtraction capability.

Any vendor that can classify a document and pull structured fields
out of it (Nutrient DWS, a mock, or something else later) implements
this Protocol. Services must only ever depend on this interface.
"""
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class ExtractedField:
    name: str
    value: str
    confidence: float  # 0.0 - 1.0


@dataclass
class ExtractionResult:
    document_type: str
    document_type_confidence: float
    fields: list[ExtractedField] = field(default_factory=list)
    source_filename: str = ""


class DocumentExtractionError(Exception):
    """Normalized error for the DocumentExtraction capability.

    Adapters must catch their own vendor-specific exceptions and
    re-raise this instead, so vendor errors never leak into services.
    """


@runtime_checkable
class DocumentExtractor(Protocol):
    def extract(self, file_path: str, filename: str) -> ExtractionResult:
        """Classify a document and extract its fields with confidence scores."""
        ...
