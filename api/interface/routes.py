import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.config import settings
from api.config.settings import ALLOWED_UPLOAD_CONTENT_TYPES, MAX_UPLOAD_BYTES, SAMPLE_DOCS_DIR
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


_KNOWN_ATTACHMENT_FILENAMES = {filename for p in PERSONAS.values() for filename in p.attachments}


@router.get("/documents/{filename}")
def get_document(filename: str):
    """Serves a persona's sample attachment for preview/download.

    Only filenames that appear in a known persona's attachment list are
    servable, this is a fixed whitelist, not a general file server, so
    there's no path-traversal surface even though the path segment is
    user-supplied.
    """
    if filename not in _KNOWN_ATTACHMENT_FILENAMES:
        return err(f"Unknown document: {filename}")

    file_path = SAMPLE_DOCS_DIR / filename
    if not file_path.is_file():
        return err(f"Document not found on server: {filename}")

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=filename,
        content_disposition_type="inline",
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


@router.post("/extract")
async def extract_uploaded_document(request: Request, file: UploadFile = File(...)):
    """Proof-of-concept "try your own document" flow. The file is written
    to a temp path for the single extraction call and deleted immediately
    after, it is never persisted server-side.
    """
    rate_limit_error = check_rate_limit(request)
    if rate_limit_error:
        return rate_limit_error

    if file.content_type not in ALLOWED_UPLOAD_CONTENT_TYPES:
        return err(f"Unsupported file type: {file.content_type}. Upload a PDF, PNG, or JPEG.")

    if settings.DOCUMENT_EXTRACTOR == "mock":
        return err(
            "Uploading your own document requires a live Nutrient DWS connection "
            "(DOCUMENT_EXTRACTOR=nutrient). This demo instance is running on canned "
            "sample data only."
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        return err(f"File too large. Max size is {MAX_UPLOAD_BYTES // (1024 * 1024)}MB.")

    suffix = Path(file.filename or "upload").suffix
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        extractor = get_document_extractor()
        result = extractor.extract(tmp_path, file.filename or "upload")
    except DocumentExtractionError as exc:
        return err(str(exc))
    finally:
        if tmp_path:
            os.unlink(tmp_path)

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
