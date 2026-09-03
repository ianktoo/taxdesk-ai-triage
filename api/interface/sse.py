"""Server-Sent Events transport for long-running agent runs.

## The streaming contract

A stream is a sequence of named events, and it always ends with exactly
one terminal event:

  event: step     data: {index, agent, action, status, detail, ...}
  event: step     data: {...}
  ...
  event: result   data: {"ok": true,  "data": {...}}     <- terminal
  event: error    data: {"ok": false, "error": "..."}    <- terminal

`step` events are progress, and carry no guarantee beyond being the
steps the run recorded, in order. The terminal event carries the exact
same `{ok, data}` / `{ok, error}` envelope the non-streaming route
returns, so the project's one response contract still holds at this
boundary: a caller that ignores every `step` event and reads only the
terminal one gets precisely the non-streaming response.

That is the deliberate resolution of "one response contract everywhere"
against a protocol that is N messages rather than one. The envelope did
not change; the stream is a delivery detail in front of it.

Every streaming route has a non-streaming twin, so a client that cannot
stream (or a proxy that buffers) is never left without a way to get the
result.
"""
import json
import queue
import threading
from dataclasses import asdict
from typing import Callable, Iterator

from api.integrations.reasoning.base import AgentStep
from api.utils.response import err

# Defeats intermediary buffering. Without these an upstream proxy is
# free to hold the whole response and deliver it in one piece at the
# end, which looks exactly like working code locally and streams
# nothing in production.
SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

StepEmitter = Callable[[AgentStep], None]


def sse_event(event: str, data: dict) -> str:
    """Formats one SSE frame.

    The JSON is emitted without literal newlines so a payload can never
    be split across `data:` lines and silently reframed.
    """
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def event_stream(run: Callable[[StepEmitter], dict]) -> Iterator[str]:
    """Runs `run` on a worker thread, yielding its steps as they happen.

    `run` receives an emitter to report steps and returns the final
    response envelope (from `ok()` or `err()`), owning its own expected
    error mapping.

    A thread is used because the pipeline is synchronous: it makes
    blocking HTTP calls to the extraction and model vendors. Handing it
    a queue lets the response generator forward each step the moment it
    is recorded, instead of waiting for the whole run to return.
    """
    steps: queue.Queue = queue.Queue()
    outcome: dict = {}
    DONE = object()

    def worker() -> None:
        try:
            outcome["envelope"] = run(lambda step: steps.put(step))
        except Exception as exc:  # noqa: BLE001 - normalized below
            # An unexpected failure still has to reach the client as the
            # standard error envelope; err() redacts any secret that
            # made it into the message.
            outcome["envelope"] = err(f"Unexpected error during the run: {exc}")
        finally:
            steps.put(DONE)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    while True:
        step = steps.get()
        if step is DONE:
            break
        yield sse_event("step", asdict(step))

    thread.join()

    envelope = outcome.get("envelope") or err("The run produced no result")
    yield sse_event("result" if envelope.get("ok") else "error", envelope)
