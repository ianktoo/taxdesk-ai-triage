"""Contract for the Reasoning capability.

Anything that can take a structured task (instructions + JSON payload)
and return structured JSON implements this Protocol: an LLM vendor, a
local model, or a deterministic mock.

Agents depend on this interface only. No agent, service, or route may
import a model vendor's SDK directly.

Note the deliberate shape: a Reasoner does not stream free text, it
answers one bounded question with one JSON object. That keeps every
agent's output parseable, testable, and cheap to validate, and it keeps
the orchestrator, rather than the model, in control of what happens
next.
"""
from dataclasses import dataclass, field
from typing import Callable, Protocol, runtime_checkable


@dataclass
class ReasoningRequest:
    """One bounded question for a reasoner.

    `task` is a short stable id ("classify", "compare", ...). The mock
    adapter dispatches on it, and it is what shows up in the trace, so
    it must stay stable even if the wording of `instructions` changes.
    """

    task: str
    instructions: str
    payload: dict
    schema_hint: str


@dataclass
class ReasoningResult:
    data: dict
    # Which model produced this, surfaced in the observability trace so a
    # reviewer can tell a real inference apart from a mock fallback.
    model: str = ""


class ReasoningError(Exception):
    """Normalized error for the Reasoning capability.

    Adapters catch their own vendor exceptions and re-raise this, so
    vendor errors never leak into agents.
    """


@runtime_checkable
class Reasoner(Protocol):
    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        """Answer one bounded task, returning parsed JSON."""
        ...


@dataclass
class AgentStep:
    """One observable action taken during a run.

    Every delegation, tool call, model call and deterministic decision
    appends one of these. This is the observability contract: if an
    action is not represented here, it did not happen as far as the UI
    is concerned.
    """

    index: int
    agent: str  # "orchestrator" | "classifier" | "comparison" | ...
    action: str  # "delegate" | "tool_call" | "reason" | "decide"
    status: str  # "ok" | "error" | "fallback" | "skipped"
    detail: str
    duration_ms: int = 0
    # Empty for deterministic steps that never called a model.
    model: str = ""


@dataclass
class AgentTrace:
    """Ordered record of every step in one orchestrated run.

    `on_step` lets a caller observe steps as they are recorded rather
    than only reading `steps` at the end. It is what makes the run
    streamable: the orchestrator does not know or care whether anyone
    is watching, so nothing about the pipeline changes when someone is.
    """

    steps: list[AgentStep] = field(default_factory=list)
    on_step: Callable[[AgentStep], None] | None = None

    def record(
        self,
        agent: str,
        action: str,
        status: str,
        detail: str,
        duration_ms: int = 0,
        model: str = "",
    ) -> AgentStep:
        step = AgentStep(
            index=len(self.steps),
            agent=agent,
            action=action,
            status=status,
            detail=detail,
            duration_ms=duration_ms,
            model=model,
        )
        self.steps.append(step)
        if self.on_step is not None:
            # An observer must never be able to break the run it is
            # watching: a broken pipe or a slow consumer stops the
            # streaming, not the triage.
            try:
                self.on_step(step)
            except Exception:
                self.on_step = None
        return step
