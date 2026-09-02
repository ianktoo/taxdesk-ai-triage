import os

os.environ.setdefault("DOCUMENT_EXTRACTOR", "mock")

from fastapi.testclient import TestClient

from api.main import app

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
