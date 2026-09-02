export const en = {
  app: {
    title: "TaxDesk AI",
    subtitle: "Attachment Triage Assistant",
    intro:
      "A simulated customer support workspace. Document classification and field extraction are powered by Nutrient DWS. All customers, messages, and documents are mock data.",
    pocNotice:
      "Proof of concept. This is a hackathon demo, not a production tax product, and it is not for real customer or financial data.",
  },
  personas: {
    heading: "Incoming customer messages",
    guide:
      "Pick a customer below to simulate them emailing in a request. Their message and attachments get sent to Nutrient DWS, which classifies each document and pulls out its key fields automatically.",
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
    statusReadyGuide:
      "Every extracted field met the confidence threshold, so this request could be actioned automatically. It still lands on the review screen below for a final human check.",
    statusReviewGuide:
      "At least one extracted field fell below the confidence threshold, so this request is held for a human to verify before anything is applied.",
    reviewReasonsHeading: "Why this needs review",
    loading: "Running documents through Nutrient DWS...",
    errorPrefix: "Triage failed:",
  },
  review: {
    heading: "Review",
    guide:
      "Check the value Nutrient DWS extracted against each attachment. Low-confidence fields are highlighted, edit any value before approving. Rejecting discards this request with no record changes.",
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
    guide: "Every triage decision made during this session, most recent last.",
    empty: "No events yet. Approve, correct, or reject a request from the Triage tab to see it show up here.",
    columnTime: "Time",
    columnPersona: "Persona",
    columnEvent: "Event",
    columnDetail: "Detail",
  },
  customerRecord: {
    heading: "Customer record",
    guide: "The mock customer record as it stands after any approved or corrected requests this session.",
    empty: "No approved updates yet. Approve a request from the Triage tab to update a customer's record.",
  },
  upload: {
    heading: "Try your own document",
    pocNotice:
      "Proof of concept: this is a hackathon demo, not a production tax product. Do not upload real personal or financial documents. Uploaded files are processed in memory for this one request only and are never stored on our servers.",
    guide: "Upload a PDF, PNG, or JPEG to see Nutrient DWS classify it and extract its fields, the same way each persona's attachments are processed.",
    chooseFile: "Choose file",
    noFileChosen: "No file chosen",
    analyzeButton: "Analyze document",
    analyzing: "Analyzing...",
    removeButton: "Remove",
    errorPrefix: "Couldn't analyze document:",
    resultHeading: "Result",
  },
  nav: {
    triage: "Triage",
    upload: "Try your own",
    auditLog: "Audit trail",
    customerRecord: "Customer record",
  },
} as const;

export type TranslationKeys = typeof en;
