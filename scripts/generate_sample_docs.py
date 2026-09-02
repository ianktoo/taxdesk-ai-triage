"""One-off generator for mock sample documents used by the demo personas.

Run with: python scripts/generate_sample_docs.py
Regenerates data/sample_docs/*.pdf. No real PII, values match the
canned extraction data in api/integrations/document_extraction/mock_adapter.py.
"""
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
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


def _write_rough_scan_pdf(filename: str, title: str, lines: list[str]):
    """Renders the doc as a low-res, noisy, slightly rotated scanned-photo
    image instead of clean vector text, so a real OCR/extraction API
    genuinely returns lower confidence on it. Used to give the demo one
    authentic low-confidence / needs-review moment instead of a faked one.
    """
    img_width, img_height = 640, 420
    image = Image.new("L", (img_width, img_height), color=235)
    draw = ImageDraw.Draw(image)

    try:
        title_font = ImageFont.truetype("arial.ttf", 22)
        body_font = ImageFont.truetype("arial.ttf", 15)
    except OSError:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    draw.text((30, 20), title, fill=40, font=title_font)
    y = 70
    for line in lines:
        draw.text((30, y), line, fill=60, font=body_font)
        y += 28

    image = image.rotate(-4, expand=True, fillcolor=235)
    image = image.filter(ImageFilter.GaussianBlur(radius=1.6))

    noise = Image.effect_noise(image.size, 28).convert("L")
    image = Image.blend(image, noise, alpha=0.12)

    image = image.resize((image.width // 2, image.height // 2)).resize(image.size)

    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=55)
    buffer.seek(0)

    path = OUT_DIR / filename
    c = canvas.Canvas(str(path), pagesize=letter)
    page_width, page_height = letter
    display_width = page_width - 144
    display_height = display_width * image.height / image.width
    c.drawImage(
        ImageReader(buffer),
        72,
        page_height - 72 - display_height,
        width=display_width,
        height=display_height,
    )
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(72, 40, "Mock document generated for demo purposes only. No real PII.")
    c.save()
    print(f"wrote {path} (rough scan)")


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
    _write_rough_scan_pdf(
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
    _write_pdf(
        "grocery_receipt.pdf",
        "Springfield Grocery Co-op - Receipt",
        [
            "Store: Springfield Grocery Co-op, 12 Main St",
            "Date: 08/28/2026",
            "Items: produce, dairy, bakery (14 items)",
            "Total: $58.34",
            "Payment method: Debit card ending 4471",
        ],
    )
    _write_pdf(
        "office_supplies_invoice.pdf",
        "Springfield Office Supply Co. - Invoice",
        [
            "Invoice number: INV-88213",
            "Bill to: Renata Silva",
            "Invoice date: 08/22/2026",
            "Amount due: $212.50",
            "Due date: 09/05/2026",
        ],
    )
    _write_pdf(
        "hoa_newsletter_letter.pdf",
        "Oakwood Commons HOA - Community Update",
        [
            "Dear resident,",
            "This month's community update covers the pool schedule,",
            "upcoming landscaping work, and the fall block party on",
            "October 3rd. No action is required on your part.",
            "Thank you, Oakwood Commons HOA Board",
        ],
    )


if __name__ == "__main__":
    main()
