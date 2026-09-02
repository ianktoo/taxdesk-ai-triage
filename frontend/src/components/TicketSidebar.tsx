import { useTranslations } from "../i18n";
import type { Ticket } from "../App";

interface Props {
  tickets: Ticket[];
  selectedTicketId: string | null;
  onSelect: (ticketId: string) => void;
}

function statusDotClass(ticket: Ticket): string {
  if (ticket.decision === "rejected") return "rejected";
  if (ticket.decision !== "pending") return "ready";
  return ticket.result.status === "ready_to_auto_approve" ? "ready" : "review";
}

function statusLabel(ticket: Ticket, labels: { statusReady: string; statusReview: string; statusApproved: string; statusCorrected: string; statusRejected: string }): string {
  if (ticket.decision === "approved") return labels.statusApproved;
  if (ticket.decision === "corrected") return labels.statusCorrected;
  if (ticket.decision === "rejected") return labels.statusRejected;
  return ticket.result.status === "ready_to_auto_approve" ? labels.statusReady : labels.statusReview;
}

export function TicketSidebar({ tickets, selectedTicketId, onSelect }: Props) {
  const t = useTranslations();
  const sorted = [...tickets].sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1));

  return (
    <aside className="sidebar" aria-label={t.queue.heading}>
      <div className="sidebar-header">
        <h2>{t.queue.heading}</h2>
      </div>
      {sorted.length === 0 ? (
        <p className="sidebar-empty">{t.queue.empty}</p>
      ) : (
        <ul className="sidebar-list">
          {sorted.map((ticket) => (
            <li key={ticket.id}>
              <button
                type="button"
                className="sidebar-row"
                aria-current={selectedTicketId === ticket.id}
                onClick={() => onSelect(ticket.id)}
              >
                <div className="row-title">
                  <span className={`status-dot ${statusDotClass(ticket)}`} aria-hidden="true" />
                  {ticket.customerName}
                </div>
                <div className="row-subtitle">{ticket.result.request_category_label}</div>
                <div className="row-subtitle">{statusLabel(ticket, t.queue)}</div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
