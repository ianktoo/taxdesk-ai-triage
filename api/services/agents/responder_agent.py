"""Responder agent: drafts the reply the customer would receive.

The draft is a proposal, never an outbound message. Nothing in this
system sends it: it is returned alongside the triage result for the
reviewer to edit, approve, or discard, and the approval it needs is the
same human approval the record update needs. That is a product
decision, not a limitation - a model that can classify a document is
not thereby trusted to write to a customer unsupervised.
"""
from api.integrations.reasoning.base import AgentTrace, Reasoner, ReasoningRequest
from api.services.agents.base import run_agent
from api.services.agents.comparison_agent import ComparisonResult

_INSTRUCTIONS = (
    "Draft the reply this customer should receive, for a support agent to review "
    "before it is sent. Acknowledge what they asked for. If the request still "
    "needs review, say a person is checking a detail without alarming them and "
    "without blaming their documents. If anything is genuinely missing, ask for "
    "exactly that one thing. Under 90 words, warm but not chatty. Never promise "
    "a date. Never state that the change has already been made unless status is "
    "ready_to_auto_approve."
)

_SCHEMA = '{"draft_response": "the message body, greeting and sign-off included"}'

_DECISION_INSTRUCTIONS = (
    "A human reviewer has now decided this request. Draft the reply telling the "
    "customer the outcome, for that reviewer to check before it is sent.\n"
    "If decision is 'approve': confirm the change has been made. Do not mention "
    "review, checking, or documents being unclear.\n"
    "If decision is 'correct': confirm the change has been made, and state the "
    "corrected values plainly so the customer can spot an error. Do not imply "
    "they made a mistake, and do not mention confidence scores or extraction.\n"
    "If decision is 'reject': say the request was not applied, give the reason "
    "in the reason field as the explanation in your own plain words, and say "
    "what they can do next. Be direct and respectful; never blame the customer "
    "and never hide behind vague wording.\n"
    "Under 100 words. Warm, plain English. Never promise a date. State only "
    "what the payload supports."
)


def draft_decision_response(
    customer_name: str,
    category_label: str,
    decision: str,
    reason: str,
    corrections: list[dict],
    reasoner: Reasoner,
    fallback: Reasoner,
    trace: AgentTrace,
) -> str:
    """Drafts the reply for a decision a reviewer has already made.

    Separate from draft_response, which runs at triage time and can only
    hedge because nothing has been decided yet. This one knows the
    outcome, so it can state it.
    """
    payload = {
        "customer_name": customer_name,
        "category_label": category_label,
        "decision": decision,
        "reason": reason,
        "corrections": corrections,
    }

    outcome = run_agent(
        agent="responder",
        request=ReasoningRequest(
            task="respond_decision",
            instructions=_DECISION_INSTRUCTIONS,
            payload=payload,
            schema_hint=_SCHEMA,
        ),
        reasoner=reasoner,
        fallback=fallback,
        trace=trace,
        detail=f"Drafted the reply for a '{decision}' decision",
    )

    draft = str(outcome.data.get("draft_response", "")).strip()

    trace.record(
        agent="responder",
        action="decide",
        status="ok" if draft else "skipped",
        detail=(
            "Draft reply ready for the reviewer to approve before sending"
            if draft
            else "No draft produced; the reviewer will write the reply"
        ),
    )

    return draft


def draft_response(
    customer_name: str,
    category_label: str,
    status: str,
    summary: str,
    comparison: ComparisonResult,
    missing_evidence: list[str],
    reasoner: Reasoner,
    fallback: Reasoner,
    trace: AgentTrace,
) -> str:
    payload = {
        "customer_name": customer_name,
        "category_label": category_label,
        "status": status,
        "summary": summary,
        "conflicts": [c.field for c in comparison.conflicts],
        "missing_evidence": missing_evidence,
    }

    outcome = run_agent(
        agent="responder",
        request=ReasoningRequest(
            task="respond",
            instructions=_INSTRUCTIONS,
            payload=payload,
            schema_hint=_SCHEMA,
        ),
        reasoner=reasoner,
        fallback=fallback,
        trace=trace,
        detail="Drafted a customer reply for review",
    )

    draft = str(outcome.data.get("draft_response", "")).strip()

    trace.record(
        agent="responder",
        action="decide",
        status="ok" if draft else "skipped",
        detail=(
            "Draft reply ready for the reviewer to approve before sending"
            if draft
            else "No draft produced; the reviewer will write the reply"
        ),
    )

    return draft
