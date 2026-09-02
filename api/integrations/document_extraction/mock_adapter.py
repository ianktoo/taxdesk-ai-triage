"""Mock DocumentExtractor, canned responses, no network calls.

Lets the app run end-to-end with zero setup while the real Nutrient
DWS adapter is wired up. Selected via config.DOCUMENT_EXTRACTOR.
"""
from api.integrations.document_extraction.base import (
    DocumentExtractionError,
    ExtractedField,
    ExtractionResult,
)

_CANNED_RESULTS: dict[str, ExtractionResult] = {
    "change_of_address_form.pdf": ExtractionResult(
        document_type="change_of_address_form",
        document_type_confidence=0.97,
        fields=[
            ExtractedField("full_name", "Maria Alvarez", 0.96),
            ExtractedField("new_address", "123 Oak St, Springfield, IL 62704", 0.94),
            ExtractedField("effective_date", "2026-09-01", 0.91),
        ],
    ),
    "utility_bill.pdf": ExtractionResult(
        document_type="utility_bill",
        document_type_confidence=0.95,
        fields=[
            ExtractedField("account_holder_name", "Maria Alvarez", 0.93),
            ExtractedField("service_address", "123 Oak St, Springfield, IL 62704", 0.92),
            ExtractedField("billing_period", "Aug 2026", 0.88),
        ],
    ),
    "w2_2025.pdf": ExtractionResult(
        document_type="w2",
        document_type_confidence=0.98,
        fields=[
            ExtractedField("employee_name", "Maria Alvarez", 0.95),
            ExtractedField("employer_name", "Springfield Retail Co.", 0.93),
            ExtractedField("ssn_last4", "6021", 0.9),
            ExtractedField("tax_year", "2025", 0.97),
        ],
    ),
    "state_id_card.pdf": ExtractionResult(
        document_type="state_id",
        document_type_confidence=0.9,
        fields=[
            ExtractedField("full_name", "Maria Alvarez", 0.6),
            ExtractedField("address", "123 Oak St, Springfield, IL 62704", 0.55),
            ExtractedField("expiration_date", "2028-03-15", 0.7),
        ],
    ),
    "name_change_request.pdf": ExtractionResult(
        document_type="name_change_request",
        document_type_confidence=0.94,
        fields=[
            ExtractedField("previous_name", "Jasmine Whitfield", 0.92),
            ExtractedField("new_name", "Jasmine Reyes", 0.9),
            ExtractedField("effective_date", "2026-08-20", 0.87),
        ],
    ),
}


class MockDocumentExtractor:
    def extract(self, file_path: str, filename: str) -> ExtractionResult:
        result = _CANNED_RESULTS.get(filename)
        if result is None:
            raise DocumentExtractionError(f"No mock extraction data for {filename!r}")
        result.source_filename = filename
        return result
