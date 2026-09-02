"""Hardcoded customer personas for the simulation (no real inbox).

Deliberately varied: real government forms, a blank/unfilled form, and
documents unrelated to any tax action (a receipt, an invoice, a letter),
so the demo shows triage handling more than one clean happy path.
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
    "jasmine-whitfield": Persona(
        id="jasmine-whitfield",
        display_name="Jasmine Whitfield",
        message=(
            "Hi there, I got married this summer and need to update my last "
            "name on file. I've attached my name change request form."
        ),
        attachments=["name_change_request.pdf"],
    ),
    "james-okafor": Persona(
        id="james-okafor",
        display_name="James Okafor",
        message=(
            "Hi, I started a new job last month and want to make sure my "
            "withholding is set up correctly, so I've attached my signed W-4. "
            "I also meant to send in an address change form since I moved, "
            "but I think I forgot to actually fill it out before scanning it, "
            "sorry about that."
        ),
        attachments=["irs_form_w4.pdf", "irs_form_8822.pdf"],
    ),
    "renata-silva": Persona(
        id="renata-silva",
        display_name="Renata Silva",
        message=(
            "Hi, just checking on the status of my refund from last quarter. "
            "I'm also attaching a couple of receipts from that office supply "
            "run in case they're relevant, and a letter I got from my HOA "
            "that I wasn't sure where else to send."
        ),
        attachments=["office_supplies_invoice.pdf", "grocery_receipt.pdf", "hoa_newsletter_letter.pdf"],
    ),
}


def get_persona(persona_id: str) -> Persona | None:
    return PERSONAS.get(persona_id)
