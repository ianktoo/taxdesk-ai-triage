"""Shared plumbing every agent uses to reason observably.

Two invariants live here, and nowhere else, so no individual agent can
forget them:

1. Every model call is timed and appended to the trace, success or
   failure. An agent cannot reason without leaving a record.
2. A failed model call degrades to the deterministic reasoner for that
   one step rather than failing the run. The step is recorded with
   status "fallback" so the trace never pretends a model answered.
"""
import time
from dataclasses import dataclass

from api.integrations.reasoning.base import (
    AgentTrace,
    Reasoner,
    ReasoningError,
    ReasoningRequest,
)


@dataclass
class AgentOutcome:
    data: dict
    model: str
    fell_back: bool


def run_agent(
    agent: str,
    request: ReasoningRequest,
    reasoner: Reasoner,
    fallback: Reasoner,
    trace: AgentTrace,
    detail: str,
) -> AgentOutcome:
    started = time.perf_counter()
    try:
        result = reasoner.reason(request)
    except ReasoningError as exc:
        # The fallback is the deterministic reasoner, which raises only
        # for an unknown task id. Every task the agents use has a
        # handler, so a failure here is a programming error and should
        # surface rather than be swallowed as a second fallback.
        fallback_result = fallback.reason(request)
        elapsed = int((time.perf_counter() - started) * 1000)
        trace.record(
            agent=agent,
            action="reason",
            status="fallback",
            detail=f"{detail} - model call failed ({exc}); used deterministic rules instead",
            duration_ms=elapsed,
            # Names what actually produced this step. The "fallback"
            # status and the detail above already say the model call
            # failed, so this cannot be misread as an inference.
            model=fallback_result.model,
        )
        return AgentOutcome(data=fallback_result.data, model=fallback_result.model, fell_back=True)

    elapsed = int((time.perf_counter() - started) * 1000)
    trace.record(
        agent=agent,
        action="reason",
        status="ok",
        detail=detail,
        duration_ms=elapsed,
        model=result.model,
    )
    return AgentOutcome(data=result.data, model=result.model, fell_back=False)
