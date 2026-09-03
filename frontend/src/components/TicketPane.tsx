import { useState } from "react";
import { useTranslations } from "../i18n";
import { documentUrl } from "../client/apiClient";
import type { Ticket } from "../App";
import { AgentTrace } from "./AgentTrace";
import { FileIcon } from "./icons";
import { ListenButton } from "./ListenButton";
import { Spinner } from "./Spinner";

interface Props {
  ticket: Ticket;
  submitting: boolean;
  error: string | null;
  onDecision: (
    decision: "approve" | "correct" | "reject",
    fieldUpdates: Record<string, string>,
    reason: string,
    correctedFields: string[],
  ) => void;
}

type Tab = "documents" | "overview" | "trace";

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

  // The responder agent proposes; the reviewer owns the wording. Held
  // in local state so edits survive tab switches within this ticket.
  const [draft, setDraft] = useState(result.draft_response);
  const [copied, setCopied] = useState(false);

  // Rejecting asks for a reason first: it is what the customer is told
  // and what the audit trail records, so it should not be a side effect
  // of one click. Prefilled with why the system flagged the request,
  // since that is usually the reason, and always editable.
  const [rejecting, setRejecting] = useState(false);
  const [rejectReason, setRejectReason] = useState(result.review_reasons.join("; "));

  // The reply drafted for the decision just made, once one exists. The
  // parent updates this ticket in place rather than remounting, so the
  // draft arrives as a changed prop and is adopted during render —
  // reseeding from an effect would render once with a stale value.
  const [outcomeDraft, setOutcomeDraft] = useState(ticket.outcomeDraft ?? "");
  const [seededFrom, setSeededFrom] = useState(ticket.outcomeDraft);
  if (ticket.outcomeDraft !== seededFrom) {
    setSeededFrom(ticket.outcomeDraft);
    setOutcomeDraft(ticket.outcomeDraft ?? "");
  }

  async function handleCopyDraft(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard access can be denied or unavailable over plain HTTP.
      // The draft is already selectable in the textarea, so there is
      // nothing to recover from and nothing worth interrupting for.
    }
  }

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

  /** Only the fields the reviewer actually edited.
   *
   * buildFieldUpdates sends every field so the record write stays
   * complete, which means it can't be diffed to find the edits. The
   * extracted value on the ticket is the baseline to compare against.
   */
  function correctedFieldNames(): string[] {
    const names = new Set<string>();
    for (const attachment of result.attachments) {
      for (const field of attachment.extraction.fields) {
        const current = editedValues[fieldKey(attachment.filename, field.name)] ?? field.value;
        if (current !== field.value) names.add(field.name);
      }
    }
    return [...names];
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
        <button type="button" role="tab" aria-selected={tab === "trace"} onClick={() => setTab("trace")}>
          {t.ticket.tabTrace}
        </button>
      </div>

      {tab === "overview" && (
        <div>
          <h4>{t.ticket.customerMessageHeading}</h4>
          <p style={{ marginBottom: "var(--space-xs)" }}>{ticket.message}</p>
          <div style={{ marginBottom: "var(--space-md)" }}>
            <ListenButton text={ticket.message} />
          </div>

          <h4>{t.ticket.summaryHeading}</h4>
          <p className="guide-text" style={{ marginBottom: "var(--space-md)" }}>
            {result.summary}
          </p>
          {result.conflicts.length > 0 && (
            <>
              <h4>{t.ticket.conflictsHeading}</h4>
              <ul className="conflict-list">
                {result.conflicts.map((conflict) => (
                  <li key={conflict.field}>
                    <span className="conflict-field">{conflict.field.replace(/_/g, " ")}</span>
                    <ul>
                      {conflict.observations.map((observation) => (
                        <li key={observation.filename} className="mono">
                          {t.ticket.conflictSays(observation.filename, observation.value)}
                        </li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            </>
          )}

          {result.agreements.length > 0 && (
            <>
              <h4>{t.ticket.agreementsHeading}</h4>
              <ul className="agreement-list">
                {result.agreements.map((agreement) => (
                  <li key={agreement.field}>
                    <span className="conflict-field">{agreement.field.replace(/_/g, " ")}</span>{" "}
                    <span className="mono">{agreement.value}</span>{" "}
                    <span className="guide-text">{t.ticket.agreementSources(agreement.filenames.length)}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

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

          {result.draft_response && (
            <>
              <h4>{t.ticket.draftHeading}</h4>
              <p className="guide-text">{t.ticket.draftGuide}</p>
              <label className="sr-only" htmlFor="draft-response">
                {t.ticket.draftHeading}
              </label>
              <textarea
                id="draft-response"
                className="draft-response"
                rows={7}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
              />
              <div className="listen-row">
                <button type="button" onClick={() => handleCopyDraft(draft)}>
                  {copied ? t.ticket.draftCopied : t.ticket.draftCopy}
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {tab === "trace" && <AgentTrace steps={result.agent_trace} />}

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

      {resolved && ticket.outcomeDraftError && (
        <p className="banner error" role="alert">
          {t.ticket.outcomeDraftFailed} {ticket.outcomeDraftError}
        </p>
      )}

      {resolved && outcomeDraft && (
        <section className="outcome-draft">
          <h4>{t.ticket.outcomeDraftHeading}</h4>
          <p className="guide-text">{t.ticket.outcomeDraftGuide}</p>
          <label className="sr-only" htmlFor="outcome-draft">
            {t.ticket.outcomeDraftHeading}
          </label>
          <textarea
            id="outcome-draft"
            className="draft-response"
            rows={8}
            value={outcomeDraft}
            onChange={(event) => setOutcomeDraft(event.target.value)}
          />
          <div className="listen-row">
            <button type="button" onClick={() => handleCopyDraft(outcomeDraft)}>
              {copied ? t.ticket.draftCopied : t.ticket.draftCopy}
            </button>
          </div>
        </section>
      )}

      {!resolved && !rejecting && (
        <div className="action-row">
          <button
            type="button"
            className="primary"
            disabled={submitting}
            aria-busy={submitting}
            onClick={() => onDecision("approve", buildFieldUpdates(), "", [])}
          >
            {submitting && <Spinner />} {submitting ? t.ticket.submitting : t.ticket.approve}
          </button>
          <button
            type="button"
            disabled={submitting}
            aria-busy={submitting}
            onClick={() => onDecision("correct", buildFieldUpdates(), "", correctedFieldNames())}
          >
            {submitting && <Spinner />} {submitting ? t.ticket.submitting : t.ticket.correct}
          </button>
          <button type="button" className="danger" disabled={submitting} onClick={() => setRejecting(true)}>
            {t.ticket.reject}
          </button>
        </div>
      )}

      {!resolved && rejecting && (
        <section className="reject-panel">
          <label htmlFor="reject-reason">
            <strong>{t.ticket.rejectReasonLabel}</strong>
          </label>
          <p className="guide-text">{t.ticket.rejectReasonGuide}</p>
          <textarea
            id="reject-reason"
            className="draft-response"
            rows={3}
            autoFocus
            placeholder={t.ticket.rejectReasonPlaceholder}
            value={rejectReason}
            onChange={(event) => setRejectReason(event.target.value)}
          />
          <div className="action-row">
            <button
              type="button"
              className="danger"
              disabled={submitting || rejectReason.trim() === ""}
              aria-busy={submitting}
              onClick={() => onDecision("reject", {}, rejectReason.trim(), [])}
            >
              {submitting && <Spinner />} {submitting ? t.ticket.submitting : t.ticket.rejectConfirm}
            </button>
            <button type="button" disabled={submitting} onClick={() => setRejecting(false)}>
              {t.ticket.rejectCancel}
            </button>
          </div>
        </section>
      )}
    </article>
  );
}
