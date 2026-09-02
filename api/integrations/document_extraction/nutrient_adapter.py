"""Nutrient DWS adapter for the DocumentExtraction capability.

Wires the real Data Extraction API up to the DocumentExtractor contract.
Two calls per document: /extraction/classify picks the document type from
our known labels, then /extraction/extract pulls that type's fields using
a JSON Schema, with per-field confidence read from output.metadata.
Selected via config.DOCUMENT_EXTRACTOR=nutrient once NUTRIENT_DWS_API_KEY
is set.
"""
import json

import httpx

from api.config import settings
from api.integrations.document_extraction.base import (
    DocumentExtractionError,
    ExtractedField,
    ExtractionResult,
)

CLASSIFY_LABELS = [
    {
        "label": "change_of_address_form",
        "description": "A form where a customer requests to update their mailing address on file.",
    },
    {
        "label": "utility_bill",
        "description": "A utility bill (electric, gas, water, etc.) showing an account holder and service address.",
    },
    {
        "label": "w2",
        "description": "IRS Form W-2, Wage and Tax Statement.",
    },
    {
        "label": "state_id",
        "description": "A state-issued ID card or driver's license.",
    },
    {
        "label": "name_change_request",
        "description": "A form requesting a legal name change, for example after marriage.",
    },
]

EXTRACT_SCHEMAS: dict[str, dict] = {
    "change_of_address_form": {
        "type": "object",
        "properties": {
            "full_name": {"type": "string", "description": "The customer's full name"},
            "new_address": {"type": "string", "description": "The new mailing address"},
            "effective_date": {"type": "string", "description": "Effective date of the address change"},
        },
        "required": ["full_name", "new_address"],
    },
    "utility_bill": {
        "type": "object",
        "properties": {
            "account_holder_name": {"type": "string", "description": "Name on the utility account"},
            "service_address": {"type": "string", "description": "The service address on the bill"},
            "billing_period": {"type": "string", "description": "The billing period covered"},
        },
        "required": ["account_holder_name", "service_address"],
    },
    "w2": {
        "type": "object",
        "properties": {
            "employee_name": {"type": "string", "description": "Employee's full name"},
            "employer_name": {"type": "string", "description": "Employer's name"},
            "ssn_last4": {"type": "string", "description": "Last 4 digits of the employee's SSN"},
            "tax_year": {"type": "string", "description": "Tax year of the form"},
        },
        "required": ["employee_name", "employer_name"],
    },
    "state_id": {
        "type": "object",
        "properties": {
            "full_name": {"type": "string", "description": "Name on the ID"},
            "address": {"type": "string", "description": "Address on the ID"},
            "expiration_date": {"type": "string", "description": "Expiration date on the ID"},
        },
        "required": ["full_name"],
    },
    "name_change_request": {
        "type": "object",
        "properties": {
            "previous_name": {"type": "string", "description": "The previous legal name"},
            "new_name": {"type": "string", "description": "The new legal name"},
            "effective_date": {"type": "string", "description": "Effective date of the name change"},
        },
        "required": ["previous_name", "new_name"],
    },
}


class NutrientDocumentExtractor:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self._api_key = api_key or settings.NUTRIENT_DWS_API_KEY
        self._base_url = (base_url or settings.NUTRIENT_DWS_BASE_URL).rstrip("/")
        if not self._api_key:
            raise DocumentExtractionError(
                "NUTRIENT_DWS_API_KEY is not set, cannot use the nutrient adapter"
            )

    def _post(self, endpoint: str, filename: str, file_bytes: bytes, instructions: dict) -> dict:
        try:
            response = httpx.post(
                f"{self._base_url}/{endpoint}",
                headers={"Authorization": f"Bearer {self._api_key}"},
                files={"file": (filename, file_bytes, "application/octet-stream")},
                data={"instructions": json.dumps(instructions)},
                timeout=30.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise DocumentExtractionError(
                f"Nutrient DWS request to {endpoint!r} failed for {filename!r}: {exc}"
            ) from exc
        return response.json()

    def extract(self, file_path: str, filename: str) -> ExtractionResult:
        with open(file_path, "rb") as fh:
            file_bytes = fh.read()

        classify_payload = self._post(
            "extraction/classify", filename, file_bytes, {"labels": CLASSIFY_LABELS}
        )
        try:
            classification = classify_payload["output"]["classification"]
            document_type = classification["label"]
            document_type_confidence = float(classification["score"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DocumentExtractionError(
                f"Unexpected classify response shape for {filename!r}: {exc}"
            ) from exc

        schema = EXTRACT_SCHEMAS.get(document_type)
        if schema is None:
            return ExtractionResult(
                document_type=document_type,
                document_type_confidence=document_type_confidence,
                fields=[],
                source_filename=filename,
            )

        extract_payload = self._post(
            "extraction/extract",
            filename,
            file_bytes,
            {"schema": schema, "options": {"includeCitations": True}},
        )
        try:
            output = extract_payload["output"]
            data: dict = output["data"]
            metadata: dict = output.get("metadata", {})
            fields = [
                ExtractedField(
                    name=name,
                    value=str(value),
                    confidence=float(metadata.get(name, {}).get("confidence", 0.0)),
                )
                for name, value in data.items()
            ]
        except (KeyError, TypeError, ValueError) as exc:
            raise DocumentExtractionError(
                f"Unexpected extract response shape for {filename!r}: {exc}"
            ) from exc

        return ExtractionResult(
            document_type=document_type,
            document_type_confidence=document_type_confidence,
            fields=fields,
            source_filename=filename,
        )
