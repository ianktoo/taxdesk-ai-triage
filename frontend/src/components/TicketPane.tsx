import { useState } from "react";
import { useTranslations } from "../i18n";
import { documentUrl } from "../client/apiClient";
import type { Ticket } from "../App";
import { FileIcon } from "./icons";

interface Props {
  ticket: Ticket;
  submitting: boolean;
  error: string | null;
  onDecision: (decision: "approve" | "correct" | "reject", fieldUpdates: Record<string, string>) => void;
}

type Tab = "documents" | "overview";

const STATUS_MESSAGE_KEY = {
  approved: "approvedMessage",
  corrected: "correctedMessage",
  rejected: "rejectedMessage",
} as const;

function fieldKey(filename: string, name: string) {
  return `${filename}::${name}`;
}

export function TicketPane({ ticket, submitting, error, onDecision }: Props) {
  const t = useTranslations();
  const { result } = ticket;
  const isReady = result.status === "ready_to_auto_approve";
  const resolved = ticket.decision !== "pending";

  const [tab, setTab] = useState<Tab>("documents");
  const [activeAttachment, setActiveAttachment] = useState(result.attachments[0]?.filename ?? "");

  // The parent remounts this component (key={ticket.id}) whenever the
  // selected ticket changes, so this only needs to compute once per mount.
  const [editedValues, setEditedValues] = useState<Record<string, string>>(() => {
    const values: Record<string, string> = {};
    for (const attachment of result.attachments) {
      for (const field of attachment.extraction.fields) {
        values[fieldKey(attachment.filename, field.name)] = field.value;
      }
    }
    return values;
  });

  function updateField(filename: string, name: string, value: string) {
    setEditedValues((prev) => ({ ...prev, [fieldKey(filename, name)]: value }));
  }

  function buildFieldUpdates(): Record<string, string> {
    const updates: Record<string, string> = {};
    for (const attachment of result.attachments) {
      for (const field of attachment.extraction.fields) {
        updates[field.name] = editedValues[fieldKey(attachment.filename, field.name)] ?? field.value;
      }
    }
    return updates;
  }

  const currentAttachment = result.attachments.find((a) => a.filename === activeAttachment) ?? result.attachments[0];

  return (
    <article>
      <div className="message-header">
        <div>
          <h1>{ticket.customerName}</h1>
          <p className="from-line">{result.request_category_label}</p>
        </div>
        <span className={`status-badge ${isReady ? "ready" : "review"}`}>
          {isReady ? t.queue.statusReady : t.queue.statusReview}
        </span>
      </div>

      {resolved && (
        <p className="banner notice" role="status">
          {t.ticket.resolvedNotice}
        </p>
      )}

      <div className="tab-row" role="tablist">
        <button type="button" role="tab" aria-selected={tab === "documents"} onClick={() => setTab("documents")}>
          {t.ticket.tabDocuments}
        </button>
        <button type="button" role="tab" aria-selected={tab === "overview"} onClick={() => setTab("overview")}>
          {t.ticket.tabOverview}
        </button>
      </div>

      {tab === "overview" && (
        <div>
          <p className="guide-text" style={{ marginBottom: "var(--space-md)" }}>
            {result.summary}
          </p>
          {!isReady && result.review_reasons.length > 0 && (
            <>
              <h4>{t.ticket.reviewReasonsHeading}</h4>
              <ul>
                {result.review_reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      {tab === "documents" && currentAttachment && (
        <div>
          <div className="doc-tab-row" role="tablist">
            {result.attachments.map((attachment) => (
              <button
                key={attachment.filename}
                type="button"
                role="tab"
                aria-selected={attachment.filename === currentAttachment.filename}
                onClick={() => setActiveAttachment(attachment.filename)}
              >
                {attachment.filename}
              </button>
            ))}
          </div>

          <a
            className="doc-preview-card"
            href={documentUrl(currentAttachment.filename)}
            target="_blank"
            rel="noopener noreferrer"
          >
            <span className="doc-preview-icon">
              <FileIcon />
            </span>
            <div className="doc-preview-meta">
              <div className="filename">{currentAttachment.filename}</div>
              <div className="doctype">
                {t.ticket.documentType}: {currentAttachment.extraction.document_type} (
                {(currentAttachment.extraction.document_type_confidence * 100).toFixed(0)}%)
              </div>
            </div>
            <span className="doc-preview-action">{t.ticket.viewDocument}</span>
          </a>

          <table className="field-table">
            <thead>
              <tr>
                <th scope="col">{t.ticket.fieldColumn}</th>
                <th scope="col">{t.ticket.valueColumn}</th>
                <th scope="col">{t.ticket.confidenceColumn}</th>
              </tr>
            </thead>
            <tbody>
              {currentAttachment.extraction.fields.map((field) => {
                const isLow = currentAttachment.low_confidence_fields.includes(field.name);
                const inputId = `${currentAttachment.filename}-${field.name}`;
                return (
                  <tr key={field.name}>
                    <td className="field-name">
                      <label htmlFor={inputId}>{field.name.replace(/_/g, " ")}</label>
                    </td>
                    <td>
                      <input
                        id={inputId}
                        type="text"
                        disabled={resolved}
                        value={editedValues[fieldKey(currentAttachment.filename, field.name)] ?? field.value}
                        onChange={(event) => updateField(currentAttachment.filename, field.name, event.target.value)}
                      />
                    </td>
                    <td className={`field-confidence mono ${isLow ? "low" : ""}`}>
                      {(field.confidence * 100).toFixed(0)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {error && (
        <p role="alert" className="banner error">
          {t.ticket.decisionErrorPrefix} {error}
        </p>
      )}

      {resolved && (
        <p className="banner success" role="status">
          {t.ticket[STATUS_MESSAGE_KEY[ticket.decision as keyof typeof STATUS_MESSAGE_KEY]]}
        </p>
      )}

      {!resolved && (
        <div className="action-row">
          <button
            type="button"
            className="primary"
            disabled={submitting}
            aria-busy={submitting}
            onClick={() => onDecision("approve", buildFieldUpdates())}
          >
            {submitting ? t.ticket.submitting : t.ticket.approve}
          </button>
          <button
            type="button"
            disabled={submitting}
            aria-busy={submitting}
            onClick={() => onDecision("correct", buildFieldUpdates())}
          >
            {submitting ? t.ticket.submitting : t.ticket.correct}
          </button>
          <button
            type="button"
            className="danger"
            disabled={submitting}
            aria-busy={submitting}
            onClick={() => onDecision("reject", {})}
          >
            {submitting ? t.ticket.submitting : t.ticket.reject}
          </button>
        </div>
      )}
    </article>
  );
}
