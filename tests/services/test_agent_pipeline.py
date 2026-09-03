"""Tests for the agent pipeline.

The load-bearing property under test is that agents cannot talk their
way past the deterministic gate. Several tests deliberately hand the
orchestrator a reasoner that says everything is fine, and assert the
request is held anyway.
"""
import pytest

from api.data.personas import Persona
from api.integrations.document_extraction.base import ExtractedField, ExtractionResult
from api.integrations.reasoning.base import AgentTrace, ReasoningError, ReasoningRequest, ReasoningResult
from api.integrations.reasoning.mock_adapter import MOCK_MODEL_NAME, MockReasoner
from api.services.agents import classifier_agent, comparison_agent
from api.services.agents.base import run_agent
from api.services.orchestrator_service import run_agentic_triage, run_decision_response
from api.services.triage_service import AttachmentResult

HIGH = 0.97
LOW = 0.40


def attachment(filename: str, doc_type: str, fields: dict[str, tuple[str, float]], type_confidence=HIGH):
    return AttachmentResult(
        filename=filename,
        extraction=ExtractionResult(
            document_type=doc_type,
            document_type_confidence=type_confidence,
            fields=[ExtractedField(name=n, value=v, confidence=c) for n, (v, c) in fields.items()],
            source_filename=filename,
        ),
        low_confidence_fields=[n for n, (_, c) in fields.items() if c < 0.85],
    )


class ScriptedReasoner:
    """Returns a canned answer per task, and records what it was asked."""

    def __init__(self, answers: dict[str, dict]):
        self._answers = answers
        self.seen: list[ReasoningRequest] = []

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        self.seen.append(request)
        if request.task not in self._answers:
            raise ReasoningError(f"no scripted answer for {request.task}")
        return ReasoningResult(data=self._answers[request.task], model="scripted")


class FailingReasoner:
    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        raise ReasoningError("upstream is down")


# --- comparison agent: the capability that did not exist before -------------


def test_comparison_flags_documents_that_disagree():
    result = comparison_agent.compare(
        [
            attachment("form.pdf", "change_of_address_form", {"new_address": ("123 Main St", HIGH)}),
            attachment("bill.pdf", "utility_bill", {"service_address": ("88 Oak Avenue", HIGH)}),
        ],
        MockReasoner(),
        MockReasoner(),
        AgentTrace(),
    )

    assert [c.field for c in result.conflicts] == ["address"]
    assert {o.value for o in result.conflicts[0].observations} == {"123 Main St", "88 Oak Avenue"}
    assert result.agreements == []


def test_comparison_records_agreement_when_documents_match():
    result = comparison_agent.compare(
        [
            attachment("form.pdf", "change_of_address_form", {"new_address": ("123 Main St", HIGH)}),
            attachment("bill.pdf", "utility_bill", {"service_address": ("123 MAIN ST.", HIGH)}),
        ],
        MockReasoner(),
        MockReasoner(),
        AgentTrace(),
    )

    # Casing and punctuation are normalized away in plain code, so this
    # never reaches a model.
    assert result.conflicts == []
    assert [a.field for a in result.agreements] == ["address"]


def test_comparison_defers_near_misses_to_the_reasoner():
    reasoner = ScriptedReasoner(
        {"compare": {"verdicts": [{"field": "address", "equivalent": True, "note": "same street"}]}}
    )
    result = comparison_agent.compare(
        [
            attachment("form.pdf", "change_of_address_form", {"new_address": ("123 Main St", HIGH)}),
            attachment("bill.pdf", "utility_bill", {"service_address": ("123 Main Street", HIGH)}),
        ],
        reasoner,
        MockReasoner(),
        AgentTrace(),
    )

    assert [r.task for r in reasoner.seen] == ["compare"]
    assert result.conflicts == []
    assert [a.field for a in result.agreements] == ["address"]


def test_comparison_treats_a_missing_verdict_as_a_conflict():
    # A reasoner that silently drops a group must not clear it.
    reasoner = ScriptedReasoner({"compare": {"verdicts": []}})
    result = comparison_agent.compare(
        [
            attachment("form.pdf", "change_of_address_form", {"new_address": ("123 Main St", HIGH)}),
            attachment("bill.pdf", "utility_bill", {"service_address": ("88 Oak Avenue", HIGH)}),
        ],
        reasoner,
        MockReasoner(),
        AgentTrace(),
    )

    assert [c.field for c in result.conflicts] == ["address"]


def test_comparison_skips_when_no_field_spans_two_documents():
    trace = AgentTrace()
    result = comparison_agent.compare(
        [attachment("w2.pdf", "w2", {"wages": ("50000", HIGH)})],
        MockReasoner(),
        MockReasoner(),
        trace,
    )

    assert result.conflicts == [] and result.agreements == []
    assert trace.steps[-1].status == "skipped"


# --- classifier agent -------------------------------------------------------


def test_classifier_rejects_a_category_outside_the_taxonomy():
    trace = AgentTrace()
    reasoner = ScriptedReasoner(
        {"classify": {"category": "buy_me_a_boat", "rationale": "", "evidence_filenames": []}}
    )
    result = classifier_agent.classify(
        "I moved house",
        [attachment("form.pdf", "change_of_address_form", {"new_address": ("123 Main St", HIGH)})],
        reasoner,
        MockReasoner(),
        trace,
    )

    assert result.category == "change_of_address"
    assert any(step.status == "fallback" for step in trace.steps)


def test_classifier_does_not_claim_document_evidence_it_did_not_cite():
    # A category reached from message wording alone must not read as
    # document-backed, or it could auto-approve with nothing behind it.
    reasoner = ScriptedReasoner(
        {"classify": {"category": "refund_status_inquiry", "rationale": "", "evidence_filenames": []}}
    )
    result = classifier_agent.classify(
        "where is my refund",
        [attachment("receipt.pdf", "grocery_receipt", {"total": ("12.40", HIGH)})],
        reasoner,
        MockReasoner(),
        AgentTrace(),
    )

    assert result.category == "refund_status_inquiry"
    assert result.has_document_evidence is False


# --- shared agent plumbing --------------------------------------------------


def test_a_failed_model_call_degrades_to_rules_and_says_so_in_the_trace():
    trace = AgentTrace()
    outcome = run_agent(
        agent="classifier",
        request=ReasoningRequest(
            task="classify",
            instructions="",
            payload={"message": "I moved", "documents": []},
            schema_hint="",
        ),
        reasoner=FailingReasoner(),
        fallback=MockReasoner(),
        trace=trace,
        detail="classify",
    )

    assert outcome.fell_back is True
    assert outcome.data["category"] == "unclassified"
    assert trace.steps[0].status == "fallback"
    # The trace names what actually produced the step, so a run backed
    # by rules is never reported as a model inference.
    assert trace.steps[0].model == MOCK_MODEL_NAME
    assert "model call failed" in trace.steps[0].detail


# --- orchestrator: the deterministic gate -----------------------------------


def persona(attachments: list[str], message="Please update my details."):
    return Persona(
        id="test-persona", display_name="Test Customer", message=message, attachments=attachments
    )


class StubExtractor:
    def __init__(self, by_filename: dict[str, AttachmentResult]):
        self._by_filename = by_filename

    def extract(self, file_path: str, filename: str) -> ExtractionResult:
        return self._by_filename[filename].extraction


def orchestrate(attachments: list[AttachmentResult], reasoner=None, message="Please update my details."):
    extractor = StubExtractor({a.filename: a for a in attachments})
    return run_agentic_triage(
        persona([a.filename for a in attachments], message),
        extractor,
        reasoner or MockReasoner(),
        MockReasoner(),
    )


def test_agreeing_high_confidence_documents_auto_approve():
    result = orchestrate(
        [
            attachment("change_of_address_form.pdf", "change_of_address_form", {"new_address": ("123 Main St", HIGH)}),
            attachment("utility_bill.pdf", "utility_bill", {"service_address": ("123 Main St", HIGH)}),
        ]
    )

    assert result.status == "ready_to_auto_approve"
    assert result.review_reasons == []
    assert result.request_category == "change_of_address"


def test_a_conflict_between_documents_forces_human_review():
    result = orchestrate(
        [
            attachment("change_of_address_form.pdf", "change_of_address_form", {"new_address": ("123 Main St", HIGH)}),
            attachment("utility_bill.pdf", "utility_bill", {"service_address": ("88 Oak Avenue", HIGH)}),
        ]
    )

    assert result.status == "needs_human_review"
    assert any("disagree" in reason for reason in result.review_reasons)
    assert [c.field for c in result.conflicts] == ["address"]


def test_low_confidence_holds_a_request_no_matter_what_the_agents_say():
    # Every agent is told to approve of everything. The vendor's own
    # confidence score is what decides, and it still holds the request.
    permissive = ScriptedReasoner(
        {
            "classify": {
                "category": "change_of_address",
                "rationale": "clear",
                "evidence_filenames": ["change_of_address_form.pdf"],
            },
            "compare": {"verdicts": []},
            "validate": {"supported": True, "missing_evidence": [], "rationale": "all good"},
            "summarize": {"summary": "Looks fine."},
            "respond": {"draft_response": "All set."},
        }
    )
    result = orchestrate(
        [attachment("change_of_address_form.pdf", "change_of_address_form", {"new_address": ("123 Main St", LOW)})],
        reasoner=permissive,
    )

    assert result.status == "needs_human_review"
    assert any("low confidence" in reason for reason in result.review_reasons)


def test_a_category_with_no_supporting_document_cannot_auto_approve():
    result = orchestrate(
        [attachment("grocery_receipt.pdf", "grocery_receipt", {"total": ("12.40", HIGH)})],
        message="Where is my refund?",
    )

    assert result.status == "needs_human_review"
    assert result.request_category == "refund_status_inquiry"


def test_an_observer_sees_every_step_as_it_is_recorded():
    seen = []
    result = run_agentic_triage(
        persona(["change_of_address_form.pdf"]),
        StubExtractor(
            {
                "change_of_address_form.pdf": attachment(
                    "change_of_address_form.pdf",
                    "change_of_address_form",
                    {"new_address": ("123 Main St", HIGH)},
                )
            }
        ),
        MockReasoner(),
        MockReasoner(),
        on_step=seen.append,
    )

    # What was streamed and what the result carries are the same steps.
    assert [s.index for s in seen] == [s.index for s in result.agent_trace]
    assert [s.detail for s in seen] == [s.detail for s in result.agent_trace]


def test_a_broken_observer_cannot_break_the_run():
    # A disconnected client must cost the stream, never the triage.
    def explode(step):
        raise BrokenPipeError("client went away")

    result = orchestrate_with_observer(explode)

    assert result.status in ("ready_to_auto_approve", "needs_human_review")
    assert result.summary and result.agent_trace


def orchestrate_with_observer(on_step):
    filename = "change_of_address_form.pdf"
    att = attachment(filename, "change_of_address_form", {"new_address": ("123 Main St", HIGH)})
    return run_agentic_triage(
        persona([filename]),
        StubExtractor({filename: att}),
        MockReasoner(),
        MockReasoner(),
        on_step=on_step,
    )


def test_every_action_is_recorded_in_the_trace():
    result = orchestrate(
        [
            attachment("change_of_address_form.pdf", "change_of_address_form", {"new_address": ("123 Main St", HIGH)}),
            attachment("utility_bill.pdf", "utility_bill", {"service_address": ("123 Main St", HIGH)}),
        ]
    )

    agents = {step.agent for step in result.agent_trace}
    assert agents == {"orchestrator", "classifier", "comparison", "validator", "summarizer", "responder"}

    # One tool call per attachment, and the routing decision.
    tool_calls = [s for s in result.agent_trace if s.action == "tool_call"]
    assert len(tool_calls) == 2
    assert any(s.agent == "orchestrator" and s.action == "decide" for s in result.agent_trace)

    # Indices are dense and ordered, so the UI can render a timeline.
    assert [s.index for s in result.agent_trace] == list(range(len(result.agent_trace)))

    # The closing step counts itself, so the trace's own summary matches
    # what the reviewer can count on screen.
    assert f"{len(result.agent_trace)} steps" in result.agent_trace[-1].detail


def test_a_run_where_every_model_call_fails_still_returns_a_complete_result():
    # The demo must survive an unreachable or misconfigured model: the
    # request degrades to the rule-based answer rather than erroring.
    result = run_agentic_triage(
        persona(["change_of_address_form.pdf"]),
        StubExtractor(
            {
                "change_of_address_form.pdf": attachment(
                    "change_of_address_form.pdf",
                    "change_of_address_form",
                    {"new_address": ("123 Main St", HIGH)},
                )
            }
        ),
        FailingReasoner(),
        MockReasoner(),
    )

    assert result.status in ("ready_to_auto_approve", "needs_human_review")
    assert result.summary and result.draft_response
    assert result.reasoner_model == MOCK_MODEL_NAME
    assert any(step.status == "fallback" for step in result.agent_trace)


# --- the reply drafted for a decision -------------------------------------


def decide(decision: str, reason: str = "", corrections=None, reasoner=None):
    return run_decision_response(
        customer_name="Maria Alvarez",
        category_label="Change of address",
        decision=decision,
        reason=reason,
        corrections=corrections or [],
        reasoner=reasoner or MockReasoner(),
        fallback=MockReasoner(),
    )


def test_rejection_reply_carries_the_reviewers_reason():
    result = decide("reject", reason="the address on the ID doesn't match the form")

    assert "address on the ID doesn't match the form" in result.draft_response
    # A rejection must not read as though the change was applied.
    assert "applied your" not in result.draft_response


def test_rejection_without_a_reason_still_explains_itself():
    result = decide("reject")

    assert result.draft_response
    assert "verify" in result.draft_response


def test_corrected_approval_states_the_values_the_reviewer_set():
    result = decide(
        "correct",
        corrections=[{"field": "new_address", "value": "124 Main St"}],
    )

    assert "124 Main St" in result.draft_response
    assert "new address" in result.draft_response


def test_plain_approval_confirms_without_mentioning_review():
    result = decide("approve")

    assert "applied your change of address request" in result.draft_response
    assert "reviewing" not in result.draft_response


def test_decision_reply_is_traced_like_any_other_agent_action():
    result = decide("approve")

    assert [s.agent for s in result.agent_trace][0] == "orchestrator"
    assert any(s.agent == "responder" and s.action == "reason" for s in result.agent_trace)
    assert result.reasoner_model == MOCK_MODEL_NAME


def test_decision_reply_falls_back_when_the_model_is_unreachable():
    result = decide("reject", reason="documents do not match", reasoner=FailingReasoner())

    assert "documents do not match" in result.draft_response
    assert any(s.status == "fallback" for s in result.agent_trace)


def test_pipeline_produces_a_draft_reply_for_review():
    result = orchestrate(
        [attachment("change_of_address_form.pdf", "change_of_address_form", {"new_address": ("123 Main St", HIGH)})]
    )

    assert result.draft_response
    assert result.summary


def test_pipeline_handles_a_request_with_no_attachments():
    result = orchestrate([], message="Just checking in.")

    assert result.status == "needs_human_review"
    assert result.request_category == "unclassified"
    assert result.attachments == []


@pytest.mark.parametrize(
    "left,right,expect_conflict",
    [
        ("123 Main St", "123 main st", False),
        ("123 Main St", "123  Main  St.", False),
        ("123 Main St", "124 Main St", True),
    ],
)
def test_value_normalization_boundaries(left, right, expect_conflict):
    result = comparison_agent.compare(
        [
            attachment("a.pdf", "change_of_address_form", {"new_address": (left, HIGH)}),
            attachment("b.pdf", "utility_bill", {"service_address": (right, HIGH)}),
        ],
        MockReasoner(),
        MockReasoner(),
        AgentTrace(),
    )

    assert bool(result.conflicts) is expect_conflict
