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
    "irs_form_w4.pdf": ExtractionResult(
        document_type="irs_form_w4",
        document_type_confidence=0.98,
        fields=[
            ExtractedField("full_name", "James Okafor", 0.95),
            ExtractedField("address", "456 Birch Ave, Springfield, IL 62704", 0.95),
            ExtractedField("ssn_last4", "4477", 0.95),
        ],
    ),
    "irs_form_8822.pdf": ExtractionResult(
        document_type="irs_form_8822",
        document_type_confidence=0.9,
        fields=[
            ExtractedField("full_name", "", 0.3),
            ExtractedField("old_address", "", 0.3),
            ExtractedField("new_address", "", 0.3),
        ],
    ),
    "grocery_receipt.pdf": ExtractionResult(
        document_type="receipt",
        document_type_confidence=0.93,
        fields=[
            ExtractedField("merchant_name", "Springfield Grocery Co-op", 0.92),
            ExtractedField("total_amount", "$58.34", 0.9),
            ExtractedField("date", "2026-08-28", 0.88),
        ],
    ),
    "office_supplies_invoice.pdf": ExtractionResult(
        document_type="invoice",
        document_type_confidence=0.93,
        fields=[
            ExtractedField("vendor_name", "Springfield Office Supply Co.", 0.91),
            ExtractedField("invoice_number", "INV-88213", 0.9),
            ExtractedField("amount_due", "$212.50", 0.89),
        ],
    ),
    "hoa_newsletter_letter.pdf": ExtractionResult(
        document_type="letter",
        document_type_confidence=0.85,
        fields=[],
    ),
}


class MockDocumentExtractor:
    def extract(self, file_path: str, filename: str) -> ExtractionResult:
        result = _CANNED_RESULTS.get(filename)
        if result is None:
            raise DocumentExtractionError(f"No mock extraction data for {filename!r}")
        result.source_filename = filename
        return result
