"""One-off generator for mock sample documents used by the demo personas.

Run with: python scripts/generate_sample_docs.py
Regenerates data/sample_docs/*.pdf. No real PII, values match the
canned extraction data in api/integrations/document_extraction/mock_adapter.py.
"""
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "sample_docs"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _write_pdf(filename: str, title: str, lines: list[str]):
    path = OUT_DIR / filename
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, title)

    c.setFont("Helvetica", 11)
    y = height - 110
    for line in lines:
        c.drawString(72, y, line)
        y -= 20

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(72, 40, "Mock document generated for demo purposes only. No real PII.")

    c.save()
    print(f"wrote {path}")


def main():
    _write_pdf(
        "change_of_address_form.pdf",
        "Change of Address Form",
        [
            "Full name: Maria Alvarez",
            "Previous address: 88 Elm St, Springfield, IL 62703",
            "New address: 123 Oak St, Springfield, IL 62704",
            "Effective date: 09/01/2026",
            "Signature: Maria Alvarez",
        ],
    )
    _write_pdf(
        "utility_bill.pdf",
        "Springfield Power & Light - Utility Bill",
        [
            "Account holder: Maria Alvarez",
            "Service address: 123 Oak St, Springfield, IL 62704",
            "Billing period: Aug 2026",
            "Amount due: $84.12",
            "Due date: 09/15/2026",
        ],
    )
    _write_pdf(
        "w2_2025.pdf",
        "Form W-2 Wage and Tax Statement (2025)",
        [
            "Employee name: Maria Alvarez",
            "Employer name: Springfield Retail Co.",
            "SSN (last 4): XXX-XX-6021",
            "Tax year: 2025",
            "Wages, tips, other comp: $41,250.00",
        ],
    )
    _write_pdf(
        "state_id_card.pdf",
        "State ID Card (Sample)",
        [
            "Name: Maria Alvarez",
            "Address: 123 Oak St, Springfield, IL 62704",
            "DOB: 04/12/1990",
            "Expiration date: 03/15/2028",
            "ID number: IL-SAMPLE-00219",
        ],
    )
    _write_pdf(
        "name_change_request.pdf",
        "Name Change Request Form",
        [
            "Previous legal name: Jasmine Whitfield",
            "New legal name: Jasmine Reyes",
            "Reason: Marriage",
            "Effective date: 08/20/2026",
            "Supporting document referenced: Marriage certificate (attached)",
        ],
    )


if __name__ == "__main__":
    main()
