"""Validator agent: does the evidence actually support the request?

Distinct from the classifier, which asks "what is this?". This asks
"is what they attached enough to act on?" - a customer can attach four
documents, all correctly classified and all read at high confidence,
and still not have attached the one that proves the thing they asked
for.

The verdict is advisory. It can send a request to a human, and it can
name what is missing, but it cannot clear a request on its own: the
deterministic gate in the orchestrator makes that call.
"""
from dataclasses import dataclass, field

from api.integrations.reasoning.base import AgentTrace, Reasoner, ReasoningRequest
from api.services.agents.comparison_agent import FieldConflict
from api.services.triage_service import AttachmentResult

from api.services.agents.base import run_agent

_INSTRUCTIONS = (
    "Decide whether the attached documents contain enough evidence to action the "
    "stated request category without a human first gathering more. Judge only "
    "sufficiency of evidence: ignore confidence scores and field disagreements, "
    "which are handled elsewhere. If something is missing, name the missing "
    "document or field in plain language a support agent would use, not a "
    "schema name."
)

_SCHEMA = (
    '{"supported": true, "missing_evidence": ["plain-language item", ...], '
    '"rationale": "one sentence, under 25 words"}'
)


@dataclass
class Validation:
    supported: bool
    missing_evidence: list[str] = field(default_factory=list)
    rationale: str = ""


def validate(
    message: str,
    category: str,
    attachments: list[AttachmentResult],
    conflicts: list[FieldConflict],
    reasoner: Reasoner,
    fallback: Reasoner,
    trace: AgentTrace,
) -> Validation:
    payload = {
        "category": category,
        "message": message,
        "documents": [
            {
                "filename": att.filename,
                "document_type": att.extraction.document_type,
                "fields": [
                    {"name": f.name, "value": f.value} for f in att.extraction.fields
                ],
            }
            for att in attachments
        ],
        "conflicts": [conflict.field for conflict in conflicts],
    }

    outcome = run_agent(
        agent="validator",
        request=ReasoningRequest(
            task="validate",
            instructions=_INSTRUCTIONS,
            payload=payload,
            schema_hint=_SCHEMA,
        ),
        reasoner=reasoner,
        fallback=fallback,
        trace=trace,
        detail=f"Checked whether the attachments support a '{category}' request",
    )

    supported = outcome.data.get("supported") is True
    missing = [str(item).strip() for item in (outcome.data.get("missing_evidence") or []) if str(item).strip()]

    trace.record(
        agent="validator",
        action="decide",
        status="ok",
        detail=(
            "Evidence is sufficient to action the request"
            if supported
            else f"Evidence is insufficient: missing {', '.join(missing) or 'unspecified corroboration'}"
        ),
    )

    return Validation(
        supported=supported,
        missing_evidence=missing,
        rationale=str(outcome.data.get("rationale", "")).strip(),
    )
