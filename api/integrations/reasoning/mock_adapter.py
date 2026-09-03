"""Deterministic Reasoner, no network calls, no API key.

This is not a stub that returns filler. Each task is answered with the
same rule-based logic the product used before agents existed, so a
deployment with no OPENAI_API_KEY still runs the full orchestrated
pipeline end to end and still produces a real, honest trace. What it
loses is judgement on the cases rules can't reach: an unseen document
type, or two spellings of one address that a model would recognize as
the same place.

Keeping this adapter faithful is what makes the agent layer safe to
ship: the model is an upgrade over the baseline, never a dependency
the demo falls over without.
"""
from api.data.taxonomy import (
    CATEGORY_BY_DOC_TYPE,
    KNOWN_CATEGORIES,
    categorize_by_rules,
    label_for,
)
from api.integrations.reasoning.base import (
    ReasoningError,
    ReasoningRequest,
    ReasoningResult,
)

MOCK_MODEL_NAME = "mock-rules"


def _classify(payload: dict) -> dict:
    documents = payload.get("documents") or []
    document_types = [str(d.get("document_type", "")) for d in documents]
    category, has_evidence = categorize_by_rules(str(payload.get("message", "")), document_types)

    evidence = [
        str(d.get("filename", ""))
        for d in documents
        if CATEGORY_BY_DOC_TYPE.get(str(d.get("document_type", ""))) == category
    ]

    if has_evidence:
        rationale = f"Matched on document type(s): {', '.join(sorted(set(document_types)))}."
    elif category in KNOWN_CATEGORIES and category != "unclassified":
        rationale = "No attachment matched a known type; matched on message wording only."
    else:
        rationale = "Neither the attachments nor the message wording matched a known request type."

    return {"category": category, "rationale": rationale, "evidence_filenames": evidence}


def _compare(payload: dict) -> dict:
    # The comparison agent only sends groups whose normalized values
    # already disagree, so without a model there is nothing left to
    # reconcile: every group is a genuine conflict. A real reasoner is
    # what recognizes "123 Main St" and "123 Main Street" as one value.
    groups = payload.get("groups") or []
    return {
        "verdicts": [
            {
                "field": str(group.get("field", "")),
                "equivalent": False,
                "note": "Values differ and no reasoner was available to judge equivalence.",
            }
            for group in groups
        ]
    }


def _validate(payload: dict) -> dict:
    category = str(payload.get("category", ""))
    documents = payload.get("documents") or []
    document_types = [str(d.get("document_type", "")) for d in documents]

    rules_category, has_evidence = categorize_by_rules(str(payload.get("message", "")), document_types)
    supported = has_evidence and rules_category == category

    missing: list[str] = []
    if not supported:
        missing.append(f"a document that confirms '{label_for(category)}'")

    return {
        "supported": supported,
        "missing_evidence": missing,
        "rationale": (
            "An attached document matches the request type."
            if supported
            else "No attachment corroborates the request type; a human must verify it."
        ),
    }


def _summarize(payload: dict) -> dict:
    name = str(payload.get("customer_name", "The customer"))
    label = str(payload.get("category_label", "Unclassified")).lower()
    agreements = payload.get("agreements") or []
    conflicts = payload.get("conflicts") or []

    parts = [f"{name} submitted a {label} request."]

    if agreements:
        first = agreements[0]
        field_name = str(first.get("field", "a field")).replace("_", " ")
        sources = len(first.get("filenames") or [])
        if sources > 1:
            parts.append(f"{sources} documents agree on {field_name} ({first.get('value')}).")
        else:
            parts.append(f"Extracted {field_name}: {first.get('value')}.")

    if conflicts:
        names = ", ".join(str(c).replace("_", " ") for c in conflicts)
        parts.append(f"Documents disagree on {names}.")

    documents = payload.get("documents") or []
    if not documents:
        parts.append("No attachments were provided.")

    return {"summary": " ".join(parts)}


def _respond(payload: dict) -> dict:
    name = str(payload.get("customer_name", "there")).split(" ")[0]
    label = str(payload.get("category_label", "request")).lower()
    needs_review = str(payload.get("status", "")) == "needs_human_review"

    if needs_review:
        body = (
            f"Thanks for sending this over. We've received your {label} request and the "
            "documents you attached. A member of our team is reviewing a couple of details "
            "before we apply the change, and we'll confirm as soon as that's done."
        )
    else:
        body = (
            f"Thanks for sending this over. We've received your {label} request and the "
            "attached documents confirm the details, so we're applying the change now. "
            "You'll see it reflected on your account shortly."
        )

    return {"draft_response": f"Hi {name},\n\n{body}\n\nBest regards,\nTaxDesk Support"}


def _respond_decision(payload: dict) -> dict:
    name = str(payload.get("customer_name", "there")).split(" ")[0]
    label = str(payload.get("category_label", "request")).lower()
    decision = str(payload.get("decision", ""))
    reason = str(payload.get("reason", "")).strip()
    corrections = payload.get("corrections") or []

    if decision == "reject":
        explanation = reason or "we weren't able to verify the details against the documents provided"
        body = (
            f"Thanks for getting in touch about your {label} request. We haven't been "
            f"able to apply this change, because {explanation.rstrip('.')}. If you can "
            "send us an updated document, we'll be glad to take another look."
        )
    elif decision == "correct" and corrections:
        listed = "; ".join(
            f"{str(c.get('field', '')).replace('_', ' ')}: {c.get('value')}" for c in corrections
        )
        body = (
            f"Thanks for sending this over. We've applied your {label} request. "
            f"Please check the details we've recorded — {listed} — and let us know "
            "straight away if anything looks wrong."
        )
    else:
        body = (
            f"Thanks for sending this over. We've applied your {label} request, and "
            "you'll see it reflected on your account shortly."
        )

    return {"draft_response": f"Hi {name},\n\n{body}\n\nBest regards,\nTaxDesk Support"}


_HANDLERS = {
    "classify": _classify,
    "compare": _compare,
    "validate": _validate,
    "summarize": _summarize,
    "respond": _respond,
    "respond_decision": _respond_decision,
}


class MockReasoner:
    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        handler = _HANDLERS.get(request.task)
        if handler is None:
            raise ReasoningError(f"MockReasoner has no handler for task: {request.task}")
        return ReasoningResult(data=handler(request.payload), model=MOCK_MODEL_NAME)
