"""Applies a human decision to the (frontend-held) mock customer record.

Per the statelessness caveat for serverless deploys, the backend holds
no durable state: it computes what the record update and audit entry
*should* look like, and the frontend is the system of record, appending
these to its own React state.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RecordUpdate:
    customer_name: str
    field_updates: dict[str, str] = field(default_factory=dict)


@dataclass
class AuditEntry:
    timestamp: str
    persona_id: str
    event_type: str
    detail: str


def apply_decision(
    persona_id: str,
    customer_name: str,
    request_category: str,
    decision: str,  # "approve" | "correct" | "reject"
    field_updates: dict[str, str],
    reason: str = "",
    corrected_fields: list[str] | None = None,
) -> tuple[RecordUpdate | None, AuditEntry]:
    timestamp = datetime.now(timezone.utc).isoformat()
    # Which fields the reviewer actually edited, as opposed to every
    # field submitted with the decision. Falls back to the full set when
    # the caller doesn't distinguish them.
    edited = corrected_fields if corrected_fields is not None else list(field_updates.keys())

    if decision == "approve":
        record = RecordUpdate(customer_name=customer_name, field_updates=field_updates)
        audit = AuditEntry(
            timestamp=timestamp,
            persona_id=persona_id,
            event_type="approved",
            detail=f"{request_category} approved; record updated with {list(field_updates.keys())}",
        )
        return record, audit

    if decision == "correct":
        record = RecordUpdate(customer_name=customer_name, field_updates=field_updates)
        audit = AuditEntry(
            timestamp=timestamp,
            persona_id=persona_id,
            event_type="corrected_and_approved",
            detail=f"{request_category} approved after correction to {edited}",
        )
        return record, audit

    # The reason a request was turned down is the part of a rejection
    # worth auditing, so it goes in the entry rather than only into the
    # customer reply.
    audit = AuditEntry(
        timestamp=timestamp,
        persona_id=persona_id,
        event_type="rejected",
        detail=(
            f"{request_category} rejected by reviewer: {reason}"
            if reason
            else f"{request_category} rejected by reviewer"
        ),
    )
    return None, audit
