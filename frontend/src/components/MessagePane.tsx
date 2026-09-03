import { useTranslations } from "../i18n";
import { documentUrl, type PersonaSummary } from "../client/apiClient";
import type { Ticket } from "../App";
import { PaperclipIcon, SendIcon, CheckCircleIcon } from "./icons";
import { ListenButton } from "./ListenButton";
import { Spinner } from "./Spinner";

interface Props {
  persona: PersonaSummary | null;
  sending: boolean;
  error: string | null;
  lastTicket: Ticket | null;
  onSend: (personaId: string) => void;
  onViewInQueue: (ticketId: string) => void;
}

export function MessagePane({ persona, sending, error, lastTicket, onSend, onViewInQueue }: Props) {
  const t = useTranslations();

  if (!persona) {
    return <p className="main-empty">{t.message.empty}</p>;
  }

  const alreadySent = lastTicket !== null;

  return (
    <article>
      <div className="message-header">
        <div>
          <h1>{persona.display_name}</h1>
          <p className="from-line">Incoming customer request</p>
        </div>
        {!alreadySent && !sending && (
          <button type="button" className="primary" onClick={() => onSend(persona.id)}>
            <SendIcon /> {t.message.sendButton}
          </button>
        )}
        {sending && (
          <button type="button" className="primary" disabled aria-busy="true">
            <Spinner /> {t.message.sending}
          </button>
        )}
      </div>

      <p className="message-body">{persona.message}</p>
      <div style={{ marginBottom: "var(--space-md)" }}>
        <ListenButton text={persona.message} />
      </div>

      <div className="attachment-chip-list">
        {persona.attachments.map((filename) => (
          <a
            className="attachment-chip"
            key={filename}
            href={documentUrl(filename)}
            target="_blank"
            rel="noopener noreferrer"
          >
            <PaperclipIcon width={14} height={14} />
            {filename}
          </a>
        ))}
      </div>

      {sending && (
        <p className="banner notice" role="status">
          <Spinner /> {t.message.processingNotice}
        </p>
      )}

      {error && (
        <p role="alert" className="banner error">
          {t.message.errorPrefix} {error}
        </p>
      )}

      {alreadySent && (
        <div className="banner success" role="status">
          <div className="sent-notice">
            <CheckCircleIcon width={16} height={16} />
            {t.message.sentLabel}
          </div>
          <p style={{ margin: "0 0 var(--space-sm)" }}>{t.message.sentDetail}</p>
          <div className="action-row">
            <button type="button" onClick={() => onViewInQueue(lastTicket.id)}>
              {t.message.viewInQueue}
            </button>
            <button type="button" disabled={sending} onClick={() => onSend(persona.id)}>
              {sending ? (
                <>
                  <Spinner /> {t.message.sending}
                </>
              ) : (
                t.message.resendButton
              )}
            </button>
          </div>
        </div>
      )}
    </article>
  );
}
