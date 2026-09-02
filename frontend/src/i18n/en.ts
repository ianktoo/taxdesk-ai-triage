export const en = {
  app: {
    title: "TaxDesk AI",
    subtitle: "Attachment Triage Assistant",
  },
  personas: {
    heading: "Incoming customer messages",
    sendButton: "Send to triage",
    sending: "Sending...",
    attachmentsLabel: "Attachments",
    loadErrorPrefix: "Couldn't load personas:",
  },
  triage: {
    heading: "Triage result",
    summaryLabel: "Summary",
    categoryLabel: "Request category",
    statusReady: "Ready to auto-approve",
    statusReview: "Needs human review",
    reviewReasonsHeading: "Why this needs review",
    loading: "Running documents through Nutrient DWS...",
    errorPrefix: "Triage failed:",
  },
  review: {
    heading: "Review",
    attachmentHeading: "Attachment",
    extractedFieldsHeading: "Extracted fields",
    confidenceLabel: "Confidence",
    approve: "Approve",
    correct: "Correct & approve",
    reject: "Reject",
    correctionPrompt: "Update field value",
    submitting: "Submitting...",
    decisionErrorPrefix: "Couldn't submit decision:",
    approvedMessage: "Approved. Customer record updated.",
    correctedMessage: "Correction saved and approved. Customer record updated.",
    rejectedMessage: "Request rejected. No record changes made.",
  },
  auditLog: {
    heading: "Audit trail",
    empty: "No events yet.",
    columnTime: "Time",
    columnPersona: "Persona",
    columnEvent: "Event",
    columnDetail: "Detail",
  },
  customerRecord: {
    heading: "Customer record",
    empty: "No approved updates yet.",
  },
  nav: {
    triage: "Triage",
    auditLog: "Audit trail",
    customerRecord: "Customer record",
  },
} as const;

export type TranslationKeys = typeof en;
