import os
import tempfile
import uuid
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel

from api.config import settings
from api.config.settings import ALLOWED_UPLOAD_CONTENT_TYPES, MAX_UPLOAD_BYTES, SAMPLE_DOCS_DIR
from api.data.personas import PERSONAS, Persona, get_persona
from api.integrations.cache.factory import get_cache
from api.integrations.document_extraction.base import DocumentExtractionError
from api.integrations.document_extraction.factory import get_document_extractor
from api.integrations.reasoning.base import ReasoningError
from api.integrations.reasoning.factory import get_fallback_reasoner, get_reasoner
from api.integrations.speech_synthesis.base import SpeechSynthesisError
from api.integrations.speech_synthesis.factory import get_speech_synthesizer
from api.integrations.text_generation.base import TextGenerationError
from api.integrations.text_generation.factory import get_text_generator
from api.interface.rate_limit_guard import check_rate_limit
from api.interface.sse import SSE_HEADERS, event_stream, sse_event
from api.services.approval_service import apply_decision
from api.services.orchestrator_service import run_agentic_triage, run_decision_response
from api.services.persona_generation_service import generate_draft_persona
from api.services.speech_service import synthesize_with_cache
from api.utils.response import err, ok

router = APIRouter(prefix="/api")


def _triage(persona: Persona, on_step=None):
    """Runs one request through the agent pipeline.

    Reasoner selection is config-driven; with no OPENAI_API_KEY the
    factory hands back the deterministic reasoner and the pipeline
    still runs end to end, so this route never depends on a model
    being reachable.

    Returns the response envelope, so the streaming and non-streaming
    routes share one definition of both the result and the errors.
    """
    try:
        extractor = get_document_extractor()
        result = run_agentic_triage(
            persona, extractor, get_reasoner(), get_fallback_reasoner(), on_step=on_step
        )
    except DocumentExtractionError as exc:
        return err(str(exc))
    except ReasoningError as exc:
        return err(str(exc))

    return ok(asdict(result))


def _triage_stream(persona: Persona) -> StreamingResponse:
    """The streaming twin of _triage. Same pipeline, same envelope."""
    return StreamingResponse(
        event_stream(lambda emit: _triage(persona, on_step=emit)),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get("/personas")
def list_personas():
    return ok(
        [
            {"id": p.id, "display_name": p.display_name, "message": p.message, "attachments": p.attachments}
            for p in PERSONAS.values()
        ]
    )


def _known_sample_document_filenames() -> set[str]:
    """Every PDF actually present in data/sample_docs, this is the
    servable whitelist, not a general file server, so there's no
    path-traversal surface even though filenames are user-supplied.
    Not just persona-linked files: AI-generated personas can attach any
    sample document, not only the ones a hardcoded persona references.
    """
    if not SAMPLE_DOCS_DIR.is_dir():
        return set()
    return {p.name for p in SAMPLE_DOCS_DIR.glob("*.pdf")}


@router.get("/sample-documents")
def list_sample_documents():
    return ok(sorted(_known_sample_document_filenames()))


@router.get("/documents/{filename}")
def get_document(filename: str):
    """Serves a sample attachment for preview/download."""
    if filename not in _known_sample_document_filenames():
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


class CustomTriageRequest(BaseModel):
    customer_name: str
    message: str
    attachments: list[str] = []


def _custom_persona(body: CustomTriageRequest, request: Request) -> tuple[Persona | None, dict | None]:
    """Validates an ad-hoc triage request into a Persona.

    Returns (persona, None) or (None, error_envelope). Shared by the
    streaming and non-streaming custom routes so both enforce the same
    rate limit and the same input rules.
    """
    rate_limit_error = check_rate_limit(request)
    if rate_limit_error:
        return None, rate_limit_error

    if not body.customer_name.strip() or not body.message.strip():
        return None, err("customer_name and message are required")

    known_filenames = _known_sample_document_filenames()
    unknown = [f for f in body.attachments if f not in known_filenames]
    if unknown:
        return None, err(f"Unknown attachment(s): {', '.join(unknown)}")

    return (
        Persona(
            id=f"custom-{uuid.uuid4().hex[:8]}",
            display_name=body.customer_name.strip(),
            message=body.message.strip(),
            attachments=body.attachments,
        ),
        None,
    )


# Route registration order matters: Starlette matches in registration
# order, not by specificity. "/triage/custom" must precede
# "/triage/{persona_id}", and "/triage/custom/stream" must precede
# "/triage/{persona_id}/stream", or "custom" is captured as a literal
# persona id.


@router.post("/triage/custom")
def triage_custom(body: CustomTriageRequest, request: Request):
    """Runs triage for an ad-hoc (e.g. AI-generated) persona that isn't
    in the hardcoded PERSONAS dict. Attachments must still be real files
    from the sample document library, per [[taxdesk-ai-project]] scope:
    users pick attachments, they don't upload or invent new documents
    here (that's the separate /extract "try your own" flow).
    """
    persona, error = _custom_persona(body, request)
    if error:
        return error
    return _triage(persona)


@router.post("/triage/custom/stream")
def triage_custom_stream(body: CustomTriageRequest, request: Request):
    """Streaming twin of /triage/custom."""
    persona, error = _custom_persona(body, request)
    if error:
        # A request rejected before the pipeline starts has no steps to
        # stream. It still answers as a stream, so the client has one
        # code path: a terminal error event and nothing else.
        return StreamingResponse(
            iter([sse_event("error", error)]),
            media_type="text/event-stream",
            headers=SSE_HEADERS,
        )
    return _triage_stream(persona)


@router.post("/triage/{persona_id}")
def triage(persona_id: str, request: Request):
    rate_limit_error = check_rate_limit(request)
    if rate_limit_error:
        return rate_limit_error

    persona = get_persona(persona_id)
    if persona is None:
        return err(f"Unknown persona: {persona_id}")

    return _triage(persona)


@router.post("/triage/{persona_id}/stream")
def triage_stream(persona_id: str, request: Request):
    """Streaming twin of /triage/{persona_id}.

    Emits one `step` event per recorded agent action as it happens, then
    the same envelope the non-streaming route returns.
    """
    rate_limit_error = check_rate_limit(request)
    if rate_limit_error:
        error = rate_limit_error
    else:
        persona = get_persona(persona_id)
        error = None if persona else err(f"Unknown persona: {persona_id}")

    if error:
        return StreamingResponse(
            iter([sse_event("error", error)]),
            media_type="text/event-stream",
            headers=SSE_HEADERS,
        )

    return _triage_stream(persona)


class GeneratePersonaRequest(BaseModel):
    scenario: str


@router.post("/personas/generate")
def generate_persona(body: GeneratePersonaRequest, request: Request):
    """AI-generates a draft customer name + message from a short scenario
    the agent writes. Returns a draft only, no attachments, and nothing
    is persisted server-side; the agent picks real sample documents to
    attach afterward and sends it through /triage/custom like any
    other request.
    """
    rate_limit_error = check_rate_limit(request)
    if rate_limit_error:
        return rate_limit_error

    try:
        generator = get_text_generator()
        draft = generate_draft_persona(body.scenario, generator)
    except TextGenerationError as exc:
        return err(str(exc))
    except ValueError as exc:
        return err(str(exc))

    return ok({"display_name": draft.display_name, "message": draft.message})


class SpeechRequest(BaseModel):
    text: str


@router.post("/speech")
def synthesize_speech(body: SpeechRequest, request: Request):
    """Reads a customer message aloud. Repeat requests for the same text
    are served from cache instead of regenerating audio.
    """
    rate_limit_error = check_rate_limit(request)
    if rate_limit_error:
        return rate_limit_error

    try:
        synthesizer = get_speech_synthesizer()
        cache = get_cache()
        speech = synthesize_with_cache(body.text, synthesizer, cache)
    except SpeechSynthesisError as exc:
        return err(str(exc))
    except ValueError as exc:
        return err(str(exc))

    return Response(content=speech.audio_bytes, media_type=speech.content_type)


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
    request_category_label: str = ""
    decision: str  # "approve" | "correct" | "reject"
    field_updates: dict[str, str] = {}
    # Why the reviewer rejected it, in their words. Explains the
    # decision to the customer and to the audit trail.
    reason: str = ""
    # Only the fields the reviewer actually edited. field_updates carries
    # every field so the record write stays complete, which is why this
    # is sent separately rather than inferred from it.
    corrected_fields: list[str] = []


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
        reason=body.reason,
        corrected_fields=body.corrected_fields,
    )

    corrections = [
        {"field": name, "value": body.field_updates[name]}
        for name in body.corrected_fields
        if name in body.field_updates
    ]

    try:
        response = run_decision_response(
            customer_name=body.customer_name,
            category_label=body.request_category_label or body.request_category,
            decision=body.decision,
            reason=body.reason,
            corrections=corrections,
            reasoner=get_reasoner(),
            fallback=get_fallback_reasoner(),
        )
    except ReasoningError as exc:
        # The decision itself is already applied and audited. A failed
        # draft costs the reviewer a suggestion, not their decision, so
        # it is reported in the payload rather than as a failed request.
        return ok(
            {
                "record": asdict(record) if record else None,
                "audit_entry": asdict(audit),
                "draft_response": "",
                "draft_error": str(exc),
                "agent_trace": [],
            }
        )

    return ok(
        {
            "record": asdict(record) if record else None,
            "audit_entry": asdict(audit),
            "draft_response": response.draft_response,
            "draft_error": "",
            "agent_trace": [asdict(step) for step in response.agent_trace],
        }
    )
