from fastapi.testclient import TestClient

from api.config import settings
from api.integrations.cache.factory import get_cache
from api.integrations.document_extraction.factory import get_document_extractor
from api.integrations.rate_limit.factory import get_rate_limiter
from api.integrations.reasoning.factory import get_fallback_reasoner, get_reasoner
from api.integrations.speech_synthesis.factory import get_speech_synthesizer
from api.integrations.text_generation.factory import get_text_generator
from api.main import app

# Force the mock adapters and no-op rate limiter/cache regardless of local
# .env or import order, tests must not depend on (or spend/exhaust) live
# Nutrient, OpenAI, or Upstash credits/quota shared with manual testing.
settings.DOCUMENT_EXTRACTOR = "mock"
settings.OPENAI_API_KEY = ""
settings.UPSTASH_REDIS_REST_URL = ""
settings.UPSTASH_REDIS_REST_TOKEN = ""
settings.AGENT_REASONER = "mock"
get_document_extractor.cache_clear()
get_rate_limiter.cache_clear()
get_text_generator.cache_clear()
get_speech_synthesizer.cache_clear()
get_cache.cache_clear()
get_reasoner.cache_clear()
get_fallback_reasoner.cache_clear()

client = TestClient(app)


def test_triage_happy_path_for_known_persona():
    response = client.post("/api/triage/maria-alvarez")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["persona_id"] == "maria-alvarez"
    assert body["data"]["status"] in ("ready_to_auto_approve", "needs_human_review")


def test_triage_response_carries_the_agent_trace():
    response = client.post("/api/triage/maria-alvarez")
    data = response.json()["data"]

    assert data["agent_trace"], "the route must expose what the agents did"
    step = data["agent_trace"][0]
    assert {"index", "agent", "action", "status", "detail", "duration_ms", "model"} <= set(step)
    assert data["draft_response"]
    assert data["reasoner_model"]


def test_triage_unknown_persona_returns_contract_error():
    response = client.post("/api/triage/does-not-exist")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert "error" in body


def test_get_document_serves_known_attachment():
    response = client.get("/api/documents/change_of_address_form.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_get_document_rejects_unknown_filename():
    response = client.get("/api/documents/not-a-real-attachment.pdf")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False


def test_list_sample_documents_includes_known_filenames():
    response = client.get("/api/sample-documents")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "change_of_address_form.pdf" in body["data"]


def test_custom_triage_with_valid_attachment():
    response = client.post(
        "/api/triage/custom",
        json={
            "customer_name": "Test Customer",
            "message": "Here is my form.",
            "attachments": ["change_of_address_form.pdf"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["customer_name"] == "Test Customer"


def test_custom_triage_rejects_unknown_attachment():
    response = client.post(
        "/api/triage/custom",
        json={"customer_name": "Test Customer", "message": "Hi", "attachments": ["not_a_real_file.pdf"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False


def test_generate_persona_returns_draft_text():
    response = client.post("/api/personas/generate", json={"scenario": "Lost my refund check"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["display_name"]
    assert body["data"]["message"]


def test_synthesize_speech_returns_audio():
    response = client.post("/api/speech", json={"text": "Hello there."})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 0


def _approve(**overrides):
    body = {
        "persona_id": "maria-alvarez",
        "customer_name": "Maria Alvarez",
        "request_category": "change_of_address",
        "request_category_label": "Change of address",
        "decision": "approve",
        "field_updates": {},
        "reason": "",
        "corrected_fields": [],
    }
    body.update(overrides)
    return client.post("/api/approve", json=body).json()


def test_rejection_records_the_reason_and_explains_it_to_the_customer():
    body = _approve(decision="reject", reason="the ID address doesn't match the form")

    assert body["ok"] is True
    assert body["data"]["record"] is None
    assert "ID address doesn't match the form" in body["data"]["audit_entry"]["detail"]
    assert "ID address doesn't match the form" in body["data"]["draft_response"]


def test_corrected_approval_names_only_the_edited_fields():
    body = _approve(
        decision="correct",
        field_updates={"new_address": "124 Main St", "full_name": "Maria Alvarez"},
        corrected_fields=["new_address"],
    )

    detail = body["data"]["audit_entry"]["detail"]
    assert "new_address" in detail
    # The untouched field was still written to the record, but it was
    # not a correction and must not be reported as one.
    assert "full_name" not in detail
    assert "124 Main St" in body["data"]["draft_response"]


def test_approval_response_carries_its_own_agent_trace():
    body = _approve()

    assert body["data"]["draft_response"]
    assert body["data"]["draft_error"] == ""
    assert any(step["agent"] == "responder" for step in body["data"]["agent_trace"])


def test_approval_without_a_label_still_drafts_a_reply():
    # request_category_label is optional on the wire; the raw category
    # is a usable stand-in rather than a reason to fail.
    body = _approve(request_category_label="")

    assert body["ok"] is True
    assert body["data"]["draft_response"]


def test_upload_extract_on_mock_adapter_returns_contract_error():
    # The mock adapter has no canned data for arbitrary uploads, and the
    # route explicitly blocks uploads unless a live Nutrient connection
    # is configured, so this should fail informatively, not crash.
    response = client.post(
        "/api/extract",
        files={"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert "error" in body
