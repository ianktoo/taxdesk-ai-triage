from fastapi.testclient import TestClient

from api.config import settings
from api.integrations.document_extraction.factory import get_document_extractor
from api.integrations.rate_limit.factory import get_rate_limiter
from api.main import app

# Force the mock extractor and no-op rate limiter regardless of local .env
# or import order, tests must not depend on (or spend/exhaust) live Nutrient
# credits or a live Upstash quota shared with manual testing.
settings.DOCUMENT_EXTRACTOR = "mock"
settings.UPSTASH_REDIS_REST_URL = ""
settings.UPSTASH_REDIS_REST_TOKEN = ""
get_document_extractor.cache_clear()
get_rate_limiter.cache_clear()

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
