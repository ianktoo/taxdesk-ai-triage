"""The orchestrator: the only thing that delegates.

Agents do not call each other, and no agent decides the outcome. This
module runs the pipeline, calls the tools, records every action, and
then makes the routing decision itself in ordinary Python.

That last part is the important one. The routing key is
AUTO_APPROVE_CONFIDENCE_THRESHOLD applied to real confidence scores
from the document extraction vendor. Agents contribute reasons a
request should go to a human; nothing an agent returns can clear a
request that the deterministic checks would have held. A model asked
"how confident are you" will produce a number, and that number is not
grounded in anything the document actually said - so it is never asked.

Order of operations:
  1. extract      tool call, once per attachment (Nutrient or mock)
  2. classify     agent, which request category is this
  3. compare      agent, do the documents agree with each other
  4. validate     agent, is the evidence sufficient to act
  5. decide       deterministic, threshold + conflicts + evidence
  6. summarize    agent, the reviewer's brief
  7. respond      agent, a draft reply for the reviewer to approve
"""
import time
from dataclasses import dataclass, field
from typing import Callable

from api.config.settings import AUTO_APPROVE_CONFIDENCE_THRESHOLD, SAMPLE_DOCS_DIR
from api.data.personas import Persona
from api.data.taxonomy import label_for
from api.integrations.document_extraction.base import DocumentExtractor
from api.integrations.reasoning.base import AgentStep, AgentTrace, Reasoner
from api.services.agents import (
    classifier_agent,
    comparison_agent,
    responder_agent,
    summarizer_agent,
    validator_agent,
)
from api.services.agents.comparison_agent import FieldAgreement, FieldConflict
from api.services.triage_service import AttachmentResult


@dataclass
class AgenticTriageResult:
    """Superset of TriageResult.

    Every field the pre-agent response had keeps its name and meaning,
    so the existing frontend contract still holds; the agent additions
    are purely additive.
    """

    persona_id: str
    customer_name: str
    message: str
    request_category: str
    request_category_label: str
    summary: str
    status: str  # "ready_to_auto_approve" | "needs_human_review"
    review_reasons: list[str]
    attachments: list[AttachmentResult]

    agent_trace: list[AgentStep] = field(default_factory=list)
    agreements: list[FieldAgreement] = field(default_factory=list)
    conflicts: list[FieldConflict] = field(default_factory=list)
    draft_response: str = ""
    classifier_rationale: str = ""
    # Which model backed this run, so the UI can be honest about
    # whether a real inference or the deterministic fallback produced it.
    reasoner_model: str = ""


@dataclass
class DecisionResponse:
    """The reply drafted for a decision a reviewer has already made."""

    draft_response: str
    agent_trace: list[AgentStep] = field(default_factory=list)
    reasoner_model: str = ""


def run_decision_response(
    customer_name: str,
    category_label: str,
    decision: str,
    reason: str,
    corrections: list[dict],
    reasoner: Reasoner,
    fallback: Reasoner,
) -> DecisionResponse:
    """Drafts the customer reply for an approve/correct/reject decision.

    Runs after the human has decided, so the draft states an outcome
    instead of hedging. It remains a proposal: the reviewer edits and
    sends it, and nothing here delivers anything to a customer.
    """
    trace = AgentTrace()
    trace.record(
        agent="orchestrator",
        action="delegate",
        status="ok",
        detail=(
            f"Reviewer decision '{decision}' recorded for {customer_name}; "
            "asking the responder for a reply"
        ),
    )

    draft = responder_agent.draft_decision_response(
        customer_name,
        category_label,
        decision,
        reason,
        corrections,
        reasoner,
        fallback,
        trace,
    )

    models = [step.model for step in trace.steps if step.model]
    return DecisionResponse(
        draft_response=draft,
        agent_trace=trace.steps,
        reasoner_model=models[-1] if models else "",
    )


def _extract_attachments(
    persona: Persona, extractor: DocumentExtractor, trace: AgentTrace
) -> list[AttachmentResult]:
    """Step 1: the document tool, called once per attachment.

    Extraction is a deterministic vendor call with no judgement in it,
    so it is a tool the orchestrator invokes, not an agent it delegates
    to. It is traced identically either way - observability is about
    what happened, not about what kind of component did it.
    """
    results: list[AttachmentResult] = []

    for filename in persona.attachments:
        started = time.perf_counter()
        extraction = extractor.extract(str(SAMPLE_DOCS_DIR / filename), filename)
        elapsed = int((time.perf_counter() - started) * 1000)

        low_confidence = [
            f.name
            for f in extraction.fields
            if f.confidence < AUTO_APPROVE_CONFIDENCE_THRESHOLD
        ]
        if extraction.document_type_confidence < AUTO_APPROVE_CONFIDENCE_THRESHOLD:
            low_confidence.append("document_type")

        trace.record(
            agent="orchestrator",
            action="tool_call",
            status="ok",
            detail=(
                f"Extracted {filename}: classified as '{extraction.document_type}' "
                f"({extraction.document_type_confidence * 100:.0f}%), "
                f"{len(extraction.fields)} field(s), {len(low_confidence)} below threshold"
            ),
            duration_ms=elapsed,
        )

        results.append(
            AttachmentResult(
                filename=filename,
                extraction=extraction,
                low_confidence_fields=low_confidence,
            )
        )

    if not persona.attachments:
        trace.record(
            agent="orchestrator",
            action="tool_call",
            status="skipped",
            detail="No attachments to extract",
        )

    return results


def _decide_status(
    attachments: list[AttachmentResult],
    classification: classifier_agent.Classification,
    comparison: comparison_agent.ComparisonResult,
    validation: validator_agent.Validation,
    trace: AgentTrace,
) -> tuple[str, list[str]]:
    """Step 5: the deterministic gate. No agent input decides this."""
    reasons: list[str] = []

    for attachment in attachments:
        if attachment.low_confidence_fields:
            reasons.append(
                f"{attachment.filename}: low confidence on "
                f"{', '.join(attachment.low_confidence_fields)}"
            )

    for conflict in comparison.conflicts:
        observations = "; ".join(f"{o.filename} says '{o.value}'" for o in conflict.observations)
        reasons.append(f"documents disagree on {conflict.field.replace('_', ' ')} ({observations})")

    if not classification.has_document_evidence:
        reasons.append(
            f"no attachment confirms the '{label_for(classification.category)}' category, "
            "needs manual verification"
        )
    elif not validation.supported:
        missing = ", ".join(validation.missing_evidence) or "further corroboration"
        reasons.append(f"evidence is incomplete for this request: missing {missing}")

    status = "needs_human_review" if reasons else "ready_to_auto_approve"

    trace.record(
        agent="orchestrator",
        action="decide",
        status="ok",
        detail=(
            f"Routing decision '{status}' from {len(reasons)} blocking reason(s), "
            f"threshold {AUTO_APPROVE_CONFIDENCE_THRESHOLD:.2f} applied to vendor confidence scores"
        ),
    )

    return status, reasons


def run_agentic_triage(
    persona: Persona,
    extractor: DocumentExtractor,
    reasoner: Reasoner,
    fallback: Reasoner,
    on_step: Callable[[AgentStep], None] | None = None,
) -> AgenticTriageResult:
    """Runs the pipeline. `on_step` observes steps as they happen.

    The pipeline is identical whether or not anyone is watching: an
    observer only receives what the trace was already recording.
    """
    trace = AgentTrace(on_step=on_step)
    trace.record(
        agent="orchestrator",
        action="delegate",
        status="ok",
        detail=(
            f"Received request from {persona.display_name} with "
            f"{len(persona.attachments)} attachment(s); starting pipeline"
        ),
    )

    attachments = _extract_attachments(persona, extractor, trace)

    classification = classifier_agent.classify(
        persona.message, attachments, reasoner, fallback, trace
    )
    comparison = comparison_agent.compare(attachments, reasoner, fallback, trace)
    validation = validator_agent.validate(
        persona.message,
        classification.category,
        attachments,
        comparison.conflicts,
        reasoner,
        fallback,
        trace,
    )

    status, review_reasons = _decide_status(
        attachments, classification, comparison, validation, trace
    )

    category_label = label_for(classification.category)

    summary = summarizer_agent.summarize(
        persona.display_name,
        category_label,
        persona.message,
        attachments,
        comparison,
        status,
        reasoner,
        fallback,
        trace,
    )

    draft = responder_agent.draft_response(
        persona.display_name,
        category_label,
        status,
        summary,
        comparison,
        validation.missing_evidence,
        reasoner,
        fallback,
        trace,
    )

    # +1 counts this closing step, which is not appended until the call
    # below returns.
    trace.record(
        agent="orchestrator",
        action="delegate",
        status="ok",
        detail=f"Pipeline complete in {len(trace.steps) + 1} steps",
    )

    # The last model actually used, so a run that fell back mid-pipeline
    # is not reported as if a model answered every step.
    models = [step.model for step in trace.steps if step.model]

    return AgenticTriageResult(
        persona_id=persona.id,
        customer_name=persona.display_name,
        message=persona.message,
        request_category=classification.category,
        request_category_label=category_label,
        summary=summary,
        status=status,
        review_reasons=review_reasons,
        attachments=attachments,
        agent_trace=trace.steps,
        agreements=comparison.agreements,
        conflicts=comparison.conflicts,
        draft_response=draft,
        classifier_rationale=classification.rationale,
        reasoner_model=models[-1] if models else "",
    )
