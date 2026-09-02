from dataclasses import asdict

from fastapi import APIRouter, Request
from pydantic import BaseModel

from api.data.personas import PERSONAS, get_persona
from api.integrations.document_extraction.base import DocumentExtractionError
from api.integrations.document_extraction.factory import get_document_extractor
from api.interface.rate_limit_guard import check_rate_limit
from api.services.approval_service import apply_decision
from api.services.triage_service import run_triage
from api.utils.response import err, ok

router = APIRouter(prefix="/api")


@router.get("/personas")
def list_personas():
    return ok(
        [
            {"id": p.id, "display_name": p.display_name, "message": p.message, "attachments": p.attachments}
            for p in PERSONAS.values()
        ]
    )


@router.post("/triage/{persona_id}")
def triage(persona_id: str, request: Request):
    rate_limit_error = check_rate_limit(request)
    if rate_limit_error:
        return rate_limit_error

    persona = get_persona(persona_id)
    if persona is None:
        return err(f"Unknown persona: {persona_id}")

    try:
        extractor = get_document_extractor()
        result = run_triage(persona, extractor)
    except DocumentExtractionError as exc:
        return err(str(exc))

    return ok(asdict(result))


class ApprovalRequest(BaseModel):
    persona_id: str
    customer_name: str
    request_category: str
    decision: str  # "approve" | "correct" | "reject"
    field_updates: dict[str, str] = {}


@router.post("/approve")
def approve(body: ApprovalRequest, request: Request):
    rate_limit_error = check_rate_limit(request)
    if rate_limit_error:
        return rate_limit_error

    if body.decision not in ("approve", "correct", "reject"):
        return err(f"Unknown decision: {body.decision}")

    record, audit = apply_decision(
        persona_id=body.persona_id,
        customer_name=body.customer_name,
        request_category=body.request_category,
        decision=body.decision,
        field_updates=body.field_updates,
    )
    return ok(
        {
            "record": asdict(record) if record else None,
            "audit_entry": asdict(audit),
        }
    )
