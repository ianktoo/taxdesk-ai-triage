"""Classifier agent: decides which request category this is.

Replaces a 7-entry lookup table. The table only ever answered for
document types someone had already thought of; anything else fell
straight to "unclassified". This agent reads the customer's message
alongside the extracted document types, and is constrained to the same
closed set of categories so its answer stays actionable downstream.

The model's answer is validated against that closed set before it is
trusted. An out-of-vocabulary category is discarded in favour of the
deterministic rules, not passed through.
"""
from dataclasses import dataclass

from api.data.taxonomy import KNOWN_CATEGORIES, categorize_by_rules
from api.integrations.reasoning.base import AgentTrace, Reasoner, ReasoningRequest
from api.services.agents.base import run_agent
from api.services.triage_service import AttachmentResult

_INSTRUCTIONS = (
    "Decide which single request category the customer is asking for. Weigh the "
    "message text and the attached document types together: attachments are "
    "stronger evidence than wording, but a customer may attach documents that "
    "are irrelevant to what they actually asked. You must choose one value from "
    "allowed_categories. Use 'unclassified' when nothing fits, rather than "
    "forcing a poor match. List in evidence_filenames only the attachments that "
    "actually support your choice."
)

_SCHEMA = (
    '{"category": "one of allowed_categories", '
    '"rationale": "one sentence, under 25 words", '
    '"evidence_filenames": ["filename", ...]}'
)


@dataclass
class Classification:
    category: str
    rationale: str
    evidence_filenames: list[str]
    # True when at least one attachment corroborates the category. A
    # category with no document behind it can never auto-approve, so
    # this feeds the deterministic gate, not just the summary.
    has_document_evidence: bool


def classify(
    message: str,
    attachments: list[AttachmentResult],
    reasoner: Reasoner,
    fallback: Reasoner,
    trace: AgentTrace,
) -> Classification:
    payload = {
        "message": message,
        "documents": [
            {
                "filename": att.filename,
                "document_type": att.extraction.document_type,
                "document_type_confidence": att.extraction.document_type_confidence,
            }
            for att in attachments
        ],
        "allowed_categories": sorted(KNOWN_CATEGORIES),
    }

    outcome = run_agent(
        agent="classifier",
        request=ReasoningRequest(
            task="classify",
            instructions=_INSTRUCTIONS,
            payload=payload,
            schema_hint=_SCHEMA,
        ),
        reasoner=reasoner,
        fallback=fallback,
        trace=trace,
        detail=f"Classified request from {len(attachments)} attachment(s) and the message text",
    )

    document_types = [att.extraction.document_type for att in attachments]
    rules_category, rules_evidence = categorize_by_rules(message, document_types)

    category = str(outcome.data.get("category", "")).strip()
    if category not in KNOWN_CATEGORIES:
        trace.record(
            agent="classifier",
            action="decide",
            status="fallback",
            detail=(
                f"Model proposed '{category or 'nothing'}', which is not a known category; "
                f"kept the rule-based answer '{rules_category}'"
            ),
        )
        category = rules_category

    known_filenames = {att.filename for att in attachments}
    evidence = [
        str(name)
        for name in (outcome.data.get("evidence_filenames") or [])
        if str(name) in known_filenames
    ]

    # Evidence is judged on the attachments the agent actually cited,
    # falling back to the rules when it cited none. Auto-approval hangs
    # on this, so a category the model reached from message wording
    # alone must not read as document-backed.
    has_evidence = bool(evidence) if evidence else (rules_evidence and category == rules_category)

    trace.record(
        agent="classifier",
        action="decide",
        status="ok",
        detail=(
            f"Category '{category}'"
            + (f", supported by {', '.join(evidence)}" if evidence else ", no supporting attachment")
        ),
    )

    return Classification(
        category=category,
        rationale=str(outcome.data.get("rationale", "")).strip(),
        evidence_filenames=evidence,
        has_document_evidence=has_evidence,
    )
