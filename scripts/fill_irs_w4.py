"""Fills the real IRS Form W-4 with mock demo data (no real PII) for the
James Okafor persona. Field names (f1_01 etc.) are the IRS's own standard
AcroForm/XFA field names for this form, documented publicly and stable
across W-4 revisions.

Run with: python scripts/fill_irs_w4.py
"""
from pathlib import Path

from pypdf import PdfReader, PdfWriter

SRC = Path(__file__).resolve().parents[1] / "data" / "irs_forms" / "irs_form_w4.pdf"
OUT = Path(__file__).resolve().parents[1] / "data" / "sample_docs" / "irs_form_w4.pdf"

FIELD_VALUES = {
    "topmostSubform[0].Page1[0].Step1a[0].f1_01[0]": "James",
    "topmostSubform[0].Page1[0].Step1a[0].f1_02[0]": "Okafor",
    "topmostSubform[0].Page1[0].Step1a[0].f1_03[0]": "456 Birch Ave",
    "topmostSubform[0].Page1[0].Step1a[0].f1_04[0]": "Springfield, IL 62704",
    "topmostSubform[0].Page1[0].f1_05[0]": "XXX-XX-4477",
    "topmostSubform[0].Page1[0].c1_1[0]": "1",  # filing status: Single
}


def main():
    reader = PdfReader(str(SRC))
    writer = PdfWriter()
    writer.append(reader)

    # Drop the XFA layer so non-Adobe renderers (and DWS) read the flat
    # AcroForm text we just set, instead of the original blank XFA form.
    acroform = writer._root_object["/AcroForm"]
    if "/XFA" in acroform:
        del acroform["/XFA"]
    writer.set_need_appearances_writer(True)

    for page in writer.pages:
        writer.update_page_form_field_values(page, FIELD_VALUES, auto_regenerate=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "wb") as fh:
        writer.write(fh)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
