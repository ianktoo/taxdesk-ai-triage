"""Hardcoded customer personas for the simulation (no real inbox).

Phase 1 ships one persona; more are added in build-order step 8.
"""
from dataclasses import dataclass, field


@dataclass
class Persona:
    id: str
    display_name: str
    message: str
    attachments: list[str] = field(default_factory=list)


PERSONAS: dict[str, Persona] = {
    "maria-alvarez": Persona(
        id="maria-alvarez",
        display_name="Maria Alvarez",
        message=(
            "Hi, I just moved to a new place and need to update my address on "
            "file. I've attached the change-of-address form plus a recent "
            "utility bill as proof. Also throwing in my W-2 and ID in case "
            "you need them."
        ),
        attachments=[
            "change_of_address_form.pdf",
            "utility_bill.pdf",
            "w2_2025.pdf",
            "state_id_card.pdf",
        ],
    ),
}


def get_persona(persona_id: str) -> Persona | None:
    return PERSONAS.get(persona_id)
