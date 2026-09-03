"""Summarizer agent: writes the one-paragraph brief the reviewer reads.

Replaces an if-chain of f-strings that could only describe the handful
of categories someone had written a branch for, and that described a
change-of-address the same way whether one document supported it or
four contradicted each other.

It runs last among the analysis agents, after the status is already
decided, so it can explain a verdict rather than imply one.
"""
from api.integrations.reasoning.base import AgentTrace, Reasoner, ReasoningRequest
from api.services.agents.base import run_agent
from api.services.agents.comparison_agent import ComparisonResult
from api.services.triage_service import AttachmentResult

_INSTRUCTIONS = (
    "Write a short brief for the support agent who will review this request. "
    "Lead with what the customer wants and the key value involved. Then state "
    "what the documents corroborate, and name any disagreement explicitly. Two "
    "or three sentences, under 60 words, plain declarative English. Do not "
    "greet, do not recommend a decision, and do not restate confidence "
    "percentages - the reviewer can see those in the table."
)

_SCHEMA = '{"summary": "two to three sentences"}'


def summarize(
    customer_name: str,
    category_label: str,
    message: str,
    attachments: list[AttachmentResult],
    comparison: ComparisonResult,
    status: str,
    reasoner: Reasoner,
    fallback: Reasoner,
    trace: AgentTrace,
) -> str:
    payload = {
        "customer_name": customer_name,
        "category_label": category_label,
        "message": message,
        "status": status,
        "documents": [
            {
                "filename": att.filename,
                "document_type": att.extraction.document_type,
                "fields": [{"name": f.name, "value": f.value} for f in att.extraction.fields],
                "low_confidence_fields": att.low_confidence_fields,
            }
            for att in attachments
        ],
        "agreements": [
            {"field": a.field, "value": a.value, "filenames": a.filenames}
            for a in comparison.agreements
        ],
        "conflicts": [
            {
                "field": c.field,
                "observations": [
                    {"filename": o.filename, "value": o.value} for o in c.observations
                ],
            }
            for c in comparison.conflicts
        ],
    }

    outcome = run_agent(
        agent="summarizer",
        request=ReasoningRequest(
            task="summarize",
            instructions=_INSTRUCTIONS,
            payload=payload,
            schema_hint=_SCHEMA,
        ),
        reasoner=reasoner,
        fallback=fallback,
        trace=trace,
        detail="Wrote the reviewer brief",
    )

    summary = str(outcome.data.get("summary", "")).strip()
    if not summary:
        # An empty brief would leave the reviewer's main panel blank, so
        # fall back to naming the request rather than rendering nothing.
        summary = f"{customer_name} submitted a {category_label.lower()} request."
        trace.record(
            agent="summarizer",
            action="decide",
            status="fallback",
            detail="Model returned an empty summary; used a minimal generated one",
        )

    return summary
