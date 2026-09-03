"""Tests for the SSE streaming contract.

The property that matters is the one the contract promises: a client
that ignores every `step` event and reads only the terminal event gets
exactly what the non-streaming route returns.
"""
import json

from fastapi.testclient import TestClient

from api.config import settings
from api.integrations.cache.factory import get_cache
from api.integrations.document_extraction.factory import get_document_extractor
from api.integrations.rate_limit.factory import get_rate_limiter
from api.integrations.reasoning.factory import get_fallback_reasoner, get_reasoner
from api.integrations.speech_synthesis.factory import get_speech_synthesizer
from api.integrations.text_generation.factory import get_text_generator
from api.main import app

settings.DOCUMENT_EXTRACTOR = "mock"
settings.OPENAI_API_KEY = ""
settings.UPSTASH_REDIS_REST_URL = ""
settings.UPSTASH_REDIS_REST_TOKEN = ""
settings.AGENT_REASONER = "mock"
for factory in (
    get_document_extractor,
    get_rate_limiter,
    get_text_generator,
    get_speech_synthesizer,
    get_cache,
    get_reasoner,
    get_fallback_reasoner,
):
    factory.cache_clear()

client = TestClient(app)


def parse_sse(body: str) -> list[tuple[str, dict]]:
    """Parses a raw SSE body into (event_name, payload) pairs."""
    events = []
    for frame in body.split("\n\n"):
        if not frame.strip():
            continue
        name = ""
        data = ""
        for line in frame.splitlines():
            if line.startswith("event: "):
                name = line[len("event: ") :]
            elif line.startswith("data: "):
                data = line[len("data: ") :]
        events.append((name, json.loads(data)))
    return events


def stream(path: str, **kwargs) -> list[tuple[str, dict]]:
    response = client.post(path, **kwargs)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    return parse_sse(response.text)


def test_stream_emits_steps_then_a_terminal_result():
    events = stream("/api/triage/maria-alvarez/stream")

    names = [name for name, _ in events]
    assert names[-1] == "result"
    # Terminal event appears exactly once, and only at the end.
    assert names.count("result") == 1
    assert "error" not in names
    assert names[:-1] == ["step"] * (len(names) - 1)
    assert len(names) > 5, "a real run records more than a couple of steps"


def test_step_events_carry_the_agent_step_shape_in_order():
    events = stream("/api/triage/maria-alvarez/stream")
    steps = [payload for name, payload in events if name == "step"]

    assert [s["index"] for s in steps] == list(range(len(steps)))
    for step in steps:
        assert {"index", "agent", "action", "status", "detail", "duration_ms", "model"} <= set(step)


def test_terminal_event_matches_the_non_streaming_response():
    streamed = stream("/api/triage/maria-alvarez/stream")
    terminal = streamed[-1][1]
    plain = client.post("/api/triage/maria-alvarez").json()

    assert terminal["ok"] is True
    # The envelope is the contract; only per-run timings may differ.
    for key in ("persona_id", "status", "request_category", "review_reasons", "summary"):
        assert terminal["data"][key] == plain["data"][key]

    # The steps streamed are the same steps the envelope carries.
    streamed_steps = [payload for name, payload in streamed if name == "step"]
    assert [s["detail"] for s in streamed_steps] == [
        s["detail"] for s in terminal["data"]["agent_trace"]
    ]


def test_unknown_persona_streams_a_terminal_error_and_no_steps():
    events = stream("/api/triage/does-not-exist/stream")

    assert [name for name, _ in events] == ["error"]
    assert events[0][1]["ok"] is False


def test_custom_stream_runs_the_pipeline():
    events = stream(
        "/api/triage/custom/stream",
        json={
            "customer_name": "Test Customer",
            "message": "Here is my form.",
            "attachments": ["change_of_address_form.pdf"],
        },
    )

    assert events[-1][0] == "result"
    assert events[-1][1]["data"]["customer_name"] == "Test Customer"


def test_custom_stream_rejects_bad_input_as_a_terminal_error():
    events = stream(
        "/api/triage/custom/stream",
        json={"customer_name": "Test", "message": "Hi", "attachments": ["nope.pdf"]},
    )

    assert [name for name, _ in events] == ["error"]
    assert events[0][1]["ok"] is False


def test_stream_sets_headers_that_defeat_proxy_buffering():
    # Without these an intermediary may buffer the whole response, which
    # streams perfectly in local dev and not at all in production.
    response = client.post("/api/triage/maria-alvarez/stream")
    assert response.headers["x-accel-buffering"] == "no"
    assert "no-transform" in response.headers["cache-control"]
