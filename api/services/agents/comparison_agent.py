"""Comparison agent: cross-checks the same field across documents.

This closes the gap the product's pitch always claimed but never
implemented. Before this agent, "the utility bill confirms the address
on the form" was an assumption: the summary took the first field whose
name contained "address" and called it confirmed. Two documents stating
two different addresses produced exactly the same confident output as
two documents agreeing.

The work is split deliberately. Grouping and exact matching are done
here in plain code - cheap, deterministic, and auditable. Only genuine
near-misses go to a reasoner, because deciding that "123 Main St" and
"123 Main Street" are one address is a judgement call, and deciding
that "123 Main St" and "88 Oak Ave" are not is arithmetic.
"""
import re
from dataclasses import dataclass, field

from api.integrations.reasoning.base import AgentTrace, Reasoner, ReasoningRequest
from api.services.agents.base import run_agent
from api.services.triage_service import AttachmentResult

_INSTRUCTIONS = (
    "Each group holds the same logical field as read from two or more different "
    "documents, with values that are not character-identical. Decide whether the "
    "values refer to the same real-world thing. Formatting, abbreviation, casing, "
    "punctuation and word order differences are equivalent ('123 Main St' and "
    "'123 Main Street'). A different street, number, name, date or amount is not. "
    "When genuinely unsure, answer equivalent: false, because a false conflict "
    "costs a human thirty seconds and a missed one corrupts a customer record."
)

_SCHEMA = (
    '{"verdicts": [{"field": "the group\'s field name", "equivalent": true, '
    '"note": "one short sentence"}]}'
)

# Qualifiers that distinguish which copy of a field was read, not which
# field it is. "new_address" on a form and "service_address" on a bill
# are the same logical field for agreement purposes.
_FIELD_QUALIFIERS = ("new_", "old_", "current_", "previous_", "mailing_", "service_", "primary_")


@dataclass
class FieldObservation:
    filename: str
    value: str


@dataclass
class FieldAgreement:
    field: str
    value: str
    filenames: list[str] = field(default_factory=list)


@dataclass
class FieldConflict:
    field: str
    note: str
    observations: list[FieldObservation] = field(default_factory=list)


@dataclass
class ComparisonResult:
    agreements: list[FieldAgreement] = field(default_factory=list)
    conflicts: list[FieldConflict] = field(default_factory=list)


def _normalize_field_name(name: str) -> str:
    normalized = name.strip().lower()
    for qualifier in _FIELD_QUALIFIERS:
        if normalized.startswith(qualifier):
            normalized = normalized[len(qualifier) :]
            break
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")


def _normalize_value(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.strip().lower()).strip()


def compare(
    attachments: list[AttachmentResult],
    reasoner: Reasoner,
    fallback: Reasoner,
    trace: AgentTrace,
) -> ComparisonResult:
    # field name -> filename -> raw value. A document that repeats a
    # field keeps its first reading; the point here is agreement
    # between documents, not within one.
    groups: dict[str, dict[str, str]] = {}
    for attachment in attachments:
        for extracted in attachment.extraction.fields:
            key = _normalize_field_name(extracted.name)
            groups.setdefault(key, {}).setdefault(attachment.filename, extracted.value)

    cross_document = {key: sources for key, sources in groups.items() if len(sources) > 1}

    if not cross_document:
        trace.record(
            agent="comparison",
            action="decide",
            status="skipped",
            detail="No field appears in more than one document, so there is nothing to cross-check",
        )
        return ComparisonResult()

    result = ComparisonResult()
    candidates: list[dict] = []

    for key, sources in sorted(cross_document.items()):
        distinct = {_normalize_value(value) for value in sources.values()}
        if len(distinct) == 1:
            result.agreements.append(
                FieldAgreement(
                    field=key,
                    value=next(iter(sources.values())),
                    filenames=sorted(sources),
                )
            )
        else:
            candidates.append(
                {
                    "field": key,
                    "observations": [
                        {"filename": filename, "value": value}
                        for filename, value in sorted(sources.items())
                    ],
                }
            )

    trace.record(
        agent="comparison",
        action="decide",
        status="ok",
        detail=(
            f"{len(cross_document)} field(s) appear in multiple documents: "
            f"{len(result.agreements)} match exactly, {len(candidates)} need judgement"
        ),
    )

    if not candidates:
        return result

    outcome = run_agent(
        agent="comparison",
        request=ReasoningRequest(
            task="compare",
            instructions=_INSTRUCTIONS,
            payload={"groups": candidates},
            schema_hint=_SCHEMA,
        ),
        reasoner=reasoner,
        fallback=fallback,
        trace=trace,
        detail=f"Judged equivalence for {len(candidates)} disagreeing field(s)",
    )

    verdicts = {
        str(verdict.get("field", "")): verdict
        for verdict in (outcome.data.get("verdicts") or [])
        if isinstance(verdict, dict)
    }

    for candidate in candidates:
        key = str(candidate["field"])
        observations = [
            FieldObservation(filename=str(o["filename"]), value=str(o["value"]))
            for o in candidate["observations"]
        ]
        verdict = verdicts.get(key)
        note = str(verdict.get("note", "")).strip() if verdict else ""

        # An absent verdict is treated as a conflict on purpose: a
        # reasoner that skipped a group has not cleared it, and this
        # agent must never resolve a disagreement by omission.
        if verdict is not None and verdict.get("equivalent") is True:
            result.agreements.append(
                FieldAgreement(
                    field=key,
                    value=observations[0].value,
                    filenames=[o.filename for o in observations],
                )
            )
            trace.record(
                agent="comparison",
                action="decide",
                status="ok",
                detail=f"'{key}' differs only in formatting across documents{f': {note}' if note else ''}",
            )
        else:
            result.conflicts.append(
                FieldConflict(
                    field=key,
                    note=note or "Documents report different values for this field.",
                    observations=observations,
                )
            )
            trace.record(
                agent="comparison",
                action="decide",
                status="ok",
                detail=(
                    f"Conflict on '{key}': "
                    + "; ".join(f"{o.filename} says '{o.value}'" for o in observations)
                ),
            )

    return result
