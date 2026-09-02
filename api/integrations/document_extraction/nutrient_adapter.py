"""Nutrient DWS adapter for the DocumentExtraction capability.

Wires the Data Extraction API up to the DocumentExtractor contract.
Selected via config.DOCUMENT_EXTRACTOR=nutrient once NUTRIENT_DWS_API_KEY
is set. Endpoint/payload shape gets confirmed against real DWS docs +
a live API key in build-order phase 2. This is the integration point,
not yet verified against a real response.
"""
import httpx

from api.config import settings
from api.integrations.document_extraction.base import (
    DocumentExtractionError,
    ExtractedField,
    ExtractionResult,
)


class NutrientDocumentExtractor:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self._api_key = api_key or settings.NUTRIENT_DWS_API_KEY
        self._base_url = base_url or settings.NUTRIENT_DWS_BASE_URL
        if not self._api_key:
            raise DocumentExtractionError(
                "NUTRIENT_DWS_API_KEY is not set — cannot use the nutrient adapter"
            )

    def extract(self, file_path: str, filename: str) -> ExtractionResult:
        try:
            with open(file_path, "rb") as fh:
                response = httpx.post(
                    f"{self._base_url}/data-extraction",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    files={"file": (filename, fh, "application/octet-stream")},
                    timeout=30.0,
                )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise DocumentExtractionError(
                f"Nutrient DWS request failed for {filename!r}: {exc}"
            ) from exc

        try:
            payload = response.json()
            fields = [
                ExtractedField(
                    name=f["name"],
                    value=f["value"],
                    confidence=float(f["confidence"]),
                )
                for f in payload.get("fields", [])
            ]
            return ExtractionResult(
                document_type=payload["document_type"],
                document_type_confidence=float(payload["document_type_confidence"]),
                fields=fields,
                source_filename=filename,
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise DocumentExtractionError(
                f"Unexpected Nutrient DWS response shape for {filename!r}: {exc}"
            ) from exc
