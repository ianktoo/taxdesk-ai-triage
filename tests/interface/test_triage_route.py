from fastapi.testclient import TestClient

from api.config import settings
from api.integrations.cache.factory import get_cache
from api.integrations.document_extraction.factory import get_document_extractor
from api.integrations.rate_limit.factory import get_rate_limiter
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
get_document_extractor.cache_clear()
get_rate_limiter.cache_clear()
get_text_generator.cache_clear()
get_speech_synthesizer.cache_clear()
get_cache.cache_clear()

client = TestClient(app)


def test_triage_happy_path_for_known_persona():
    response = client.post("/api/triage/maria-alvarez")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["persona_id"] == "maria-alvarez"
    assert body["data"]["status"] in ("ready_to_auto_approve", "needs_human_review")


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
