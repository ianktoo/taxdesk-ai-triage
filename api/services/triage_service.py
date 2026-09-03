"""Business logic: rule-based attachment triage.

The deterministic baseline. `api.services.orchestrator_service` is the
agent-driven path that supersedes it for the live product; this module
stays as the behaviour that path degrades to, and it owns the
AttachmentResult/TriageResult shapes both paths return.

Talks to the DocumentExtraction capability only through its contract
(api.integrations.document_extraction.base). No vendor SDK imports here.
"""
from dataclasses import dataclass, field

from api.config.settings import AUTO_APPROVE_CONFIDENCE_THRESHOLD, SAMPLE_DOCS_DIR
from api.data.personas import Persona
from api.data.taxonomy import categorize_by_rules, label_for
from api.integrations.document_extraction.base import DocumentExtractor, ExtractionResult


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
    """Returns (category, has_document_evidence)."""
    return categorize_by_rules(message, [a.extraction.document_type for a in attachments])


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
            f"no attachment confirms the '{label_for(category)}' category, needs manual verification"
        )
    status = "needs_human_review" if review_reasons else "ready_to_auto_approve"

    return TriageResult(
        persona_id=persona.id,
        customer_name=persona.display_name,
        message=persona.message,
        request_category=category,
        request_category_label=label_for(category),
        summary=summary,
        status=status,
        review_reasons=review_reasons,
        attachments=attachment_results,
    )
