"""Business logic: attachment triage.

Talks to the DocumentExtraction capability only through its contract
(api.integrations.document_extraction.base). No vendor SDK imports here.
"""
from dataclasses import dataclass, field

from api.config.settings import AUTO_APPROVE_CONFIDENCE_THRESHOLD, SAMPLE_DOCS_DIR
from api.data.personas import Persona
from api.integrations.document_extraction.base import DocumentExtractor, ExtractionResult

# Document type -> request category this business recognizes. Types not
# listed here (receipts, invoices, letters, ...) fall through to a
# message-text check and then to "unclassified" - the system doesn't
# force every attachment into a tax-relevant bucket just because it's
# there.
_CATEGORY_BY_DOC_TYPE = {
    "change_of_address_form": "change_of_address",
    "utility_bill": "change_of_address",
    "irs_form_8822": "change_of_address",
    "name_change_request": "name_change",
    "irs_form_w4": "update_withholding",
    "w2": "document_upload",
    "state_id": "document_upload",
}

# Message-text fallback for categories no document type maps to (a
# refund inquiry usually has no attachment that proves it either way).
_CATEGORY_KEYWORDS = {
    "refund_status_inquiry": ("refund",),
}

_CATEGORY_LABELS = {
    "change_of_address": "Change of address",
    "name_change": "Name change",
    "update_withholding": "Update withholding",
    "document_upload": "Document upload",
    "refund_status_inquiry": "Refund status inquiry",
    "unclassified": "Unclassified",
}


@dataclass
class AttachmentResult:
    filename: str
    extraction: ExtractionResult
    low_confidence_fields: list[str] = field(default_factory=list)


@dataclass
class TriageResult:
    persona_id: str
    customer_name: str
    message: str
    request_category: str
    request_category_label: str
    summary: str
    status: str  # "ready_to_auto_approve" | "needs_human_review"
    review_reasons: list[str]
    attachments: list[AttachmentResult]


def _categorize(message: str, attachments: list[AttachmentResult]) -> tuple[str, bool]:
    """Returns (category, has_document_evidence). A category reached only
    via message keywords, or not reached at all, has no document backing
    it, so it can never be auto-approved: there's nothing to verify.
    """
    for att in attachments:
        category = _CATEGORY_BY_DOC_TYPE.get(att.extraction.document_type)
        if category:
            return category, True

    message_lower = message.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(keyword in message_lower for keyword in keywords):
            return category, False

    return "unclassified", False


def _build_summary(persona: Persona, category: str, attachments: list[AttachmentResult]) -> str:
    name = persona.display_name
    if category == "change_of_address":
        address_field = next(
            (
                f
                for att in attachments
                for f in att.extraction.fields
                if "address" in f.name
            ),
            None,
        )
        if address_field:
            confidence_word = "high" if address_field.confidence >= AUTO_APPROVE_CONFIDENCE_THRESHOLD else "low"
            return (
                f"Customer wants to update address to {address_field.value}. "
                f"Supporting document confirms it, confidence {confidence_word}."
            )
        return f"{name} requests a change of address; no supporting address field extracted."
    if category == "name_change":
        return f"{name} requests a name change based on the attached name-change form."
    if category == "update_withholding":
        return f"{name} wants to update federal tax withholding based on the attached W-4."
    if category == "refund_status_inquiry":
        return f"{name} is asking about the status of a refund; no document confirms or refutes this."
    if category == "document_upload":
        doc_types = ", ".join(a.extraction.document_type for a in attachments)
        return f"{name} uploaded supporting documents ({doc_types}) with no specific action requested."
    doc_types = ", ".join(a.extraction.document_type for a in attachments) or "no attachments"
    return f"{name}'s message and attachments ({doc_types}) don't match a known request category."


def run_triage(persona: Persona, extractor: DocumentExtractor) -> TriageResult:
    attachment_results: list[AttachmentResult] = []
    for filename in persona.attachments:
        file_path = str(SAMPLE_DOCS_DIR / filename)
        extraction = extractor.extract(file_path, filename)
        low_conf = [
            f.name for f in extraction.fields if f.confidence < AUTO_APPROVE_CONFIDENCE_THRESHOLD
        ]
        if extraction.document_type_confidence < AUTO_APPROVE_CONFIDENCE_THRESHOLD:
            low_conf.append("document_type")
        attachment_results.append(
            AttachmentResult(filename=filename, extraction=extraction, low_confidence_fields=low_conf)
        )

    category, has_evidence = _categorize(persona.message, attachment_results)
    summary = _build_summary(persona, category, attachment_results)

    review_reasons = [
        f"{att.filename}: low confidence on {', '.join(att.low_confidence_fields)}"
        for att in attachment_results
        if att.low_confidence_fields
    ]
    if not has_evidence:
        review_reasons.append(
            f"no attachment confirms the '{_CATEGORY_LABELS.get(category, category)}' category, needs manual verification"
        )
    status = "needs_human_review" if review_reasons else "ready_to_auto_approve"

    return TriageResult(
        persona_id=persona.id,
        customer_name=persona.display_name,
        message=persona.message,
        request_category=category,
        request_category_label=_CATEGORY_LABELS.get(category, category),
        summary=summary,
        status=status,
        review_reasons=review_reasons,
        attachments=attachment_results,
    )
