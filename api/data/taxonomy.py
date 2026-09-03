"""The request taxonomy this business recognizes.

Lives in the data layer because more than one layer needs it: the
classifier agent uses it to constrain the model to a closed set of
categories, and the mock reasoner uses it to produce the same answer
deterministically when no model is configured.

Document types not listed here (receipts, invoices, letters, ...) fall
through to a message-text check and then to "unclassified" - the system
doesn't force every attachment into a tax-relevant bucket just because
it's there.
"""

CATEGORY_BY_DOC_TYPE = {
    "change_of_address_form": "change_of_address",
    "utility_bill": "change_of_address",
    "irs_form_8822": "change_of_address",
    "name_change_request": "name_change",
    "irs_form_w4": "update_withholding",
    "w2": "document_upload",
    "state_id": "document_upload",
}

# Message-text fallback for categories no document type maps to (a
# refund inquiry usually has no attachment that proves it either way).
CATEGORY_KEYWORDS = {
    "refund_status_inquiry": ("refund",),
}

CATEGORY_LABELS = {
    "change_of_address": "Change of address",
    "name_change": "Name change",
    "update_withholding": "Update withholding",
    "document_upload": "Document upload",
    "refund_status_inquiry": "Refund status inquiry",
    "unclassified": "Unclassified",
}

# The closed set a classifier may return. Anything outside it is
# rejected and falls back to the deterministic rules.
KNOWN_CATEGORIES = frozenset(CATEGORY_LABELS)


def label_for(category: str) -> str:
    return CATEGORY_LABELS.get(category, category)


def categorize_by_rules(message: str, document_types: list[str]) -> tuple[str, bool]:
    """The deterministic baseline classifier.

    Returns (category, has_document_evidence). A category reached only
    via message keywords, or not reached at all, has no document backing
    it, so it can never be auto-approved: there's nothing to verify.

    This is both the pre-agent behaviour and the fallback whenever the
    classifier agent is unavailable or returns something unusable, so
    the product degrades to "as good as before" rather than to nothing.
    """
    for document_type in document_types:
        category = CATEGORY_BY_DOC_TYPE.get(document_type)
        if category:
            return category, True

    message_lower = message.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in message_lower for keyword in keywords):
            return category, False

    return "unclassified", False
