import { useEffect, useState } from "react";
import { I18nProvider, useTranslations } from "./i18n";
import {
  listPersonas,
  runTriage,
  submitApproval,
  type AuditEntry,
  type PersonaSummary,
  type RecordUpdate,
  type TriageResult,
} from "./client/apiClient";
import { TopNav } from "./components/TopNav";
import { ContactSidebar } from "./components/ContactSidebar";
import { MessagePane } from "./components/MessagePane";
import { TicketSidebar } from "./components/TicketSidebar";
import { TicketPane } from "./components/TicketPane";
import { UploadPanel } from "./components/UploadPanel";
import { AuditLog } from "./components/AuditLog";
import { RecordsView } from "./components/RecordsView";

export type Mode = "customer" | "agent" | "upload" | "audit" | "records";

export type TicketDecision = "pending" | "approved" | "corrected" | "rejected";

export interface Ticket {
  id: string;
  personaId: string;
  customerName: string;
  message: string;
  result: TriageResult;
  decision: TicketDecision;
  createdAt: string;
  decidedAt?: string;
}

function AppShell() {
  const t = useTranslations();

  const [personas, setPersonas] = useState<PersonaSummary[]>([]);
  const [personaLoadError, setPersonaLoadError] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("customer");

  const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(null);
  const [sendingPersonaId, setSendingPersonaId] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);

  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [customerRecords, setCustomerRecords] = useState<Record<string, RecordUpdate>>({});

  useEffect(() => {
    listPersonas().then((result) => {
      if (result.ok) {
        setPersonas(result.data);
        setSelectedPersonaId((current) => current ?? result.data[0]?.id ?? null);
      } else {
        setPersonaLoadError(result.error);
      }
    });
  }, []);

  const selectedPersona = personas.find((p) => p.id === selectedPersonaId) ?? null;
  const lastTicketForPersona = [...tickets].reverse().find((tk) => tk.personaId === selectedPersonaId) ?? null;
  const selectedTicket = tickets.find((tk) => tk.id === selectedTicketId) ?? null;
  const pendingCount = tickets.filter((tk) => tk.decision === "pending").length;

  async function handleSend(personaId: string) {
    const persona = personas.find((p) => p.id === personaId);
    if (!persona) return;

    setSendingPersonaId(personaId);
    setSendError(null);

    const result = await runTriage(personaId);
    setSendingPersonaId(null);

    if (result.ok) {
      const ticket: Ticket = {
        id: `${personaId}-${Date.now()}`,
        personaId,
        customerName: persona.display_name,
        message: persona.message,
        result: result.data,
        decision: "pending",
        createdAt: new Date().toISOString(),
      };
      setTickets((prev) => [...prev, ticket]);
    } else {
      setSendError(result.error);
    }
  }

  function handleViewInQueue(ticketId: string) {
    setSelectedTicketId(ticketId);
    setMode("agent");
  }

  async function handleDecision(
    ticket: Ticket,
    decision: "approve" | "correct" | "reject",
    fieldUpdates: Record<string, string>,
  ) {
    setSubmittingDecision(true);
    setDecisionError(null);

    const result = await submitApproval({
      persona_id: ticket.personaId,
      customer_name: ticket.customerName,
      request_category: ticket.result.request_category,
      decision,
      field_updates: decision === "reject" ? {} : fieldUpdates,
    });

    setSubmittingDecision(false);

    if (result.ok) {
      const newDecision: TicketDecision = decision === "approve" ? "approved" : decision === "correct" ? "corrected" : "rejected";
      setTickets((prev) =>
        prev.map((tk) =>
          tk.id === ticket.id ? { ...tk, decision: newDecision, decidedAt: new Date().toISOString() } : tk,
        ),
      );
      setAuditEntries((prev) => [...prev, result.data.audit_entry]);
      if (result.data.record) {
        setCustomerRecords((prev) => ({
          ...prev,
          [result.data.record!.customer_name]: result.data.record!,
        }));
      }
    } else {
      setDecisionError(result.error);
    }
  }

  return (
    <div className="app-shell">
      <TopNav mode={mode} onModeChange={setMode} pendingCount={pendingCount} />

      <div className="app-body">
        {mode === "customer" && (
          <>
            <ContactSidebar
              personas={personas}
              selectedPersonaId={selectedPersonaId}
              onSelect={setSelectedPersonaId}
            />
            <main className="main-pane">
              {personaLoadError && <p className="banner error">{personaLoadError}</p>}
              <MessagePane
                persona={selectedPersona}
                sending={sendingPersonaId === selectedPersonaId}
                error={sendingPersonaId === null ? sendError : null}
                lastTicket={lastTicketForPersona}
                onSend={handleSend}
                onViewInQueue={handleViewInQueue}
              />
            </main>
          </>
        )}

        {mode === "agent" && (
          <>
            <TicketSidebar
              tickets={tickets}
              selectedTicketId={selectedTicketId}
              onSelect={setSelectedTicketId}
            />
            <main className="main-pane">
              {selectedTicket ? (
                <TicketPane
                  key={selectedTicket.id}
                  ticket={selectedTicket}
                  submitting={submittingDecision}
                  error={decisionError}
                  onDecision={(decision, fieldUpdates) => handleDecision(selectedTicket, decision, fieldUpdates)}
                />
              ) : (
                <p className="main-empty">{tickets.length === 0 ? t.queue.empty : t.queue.selectPrompt}</p>
              )}
            </main>
          </>
        )}

        {mode === "upload" && (
          <main className="main-pane" style={{ maxWidth: 720 }}>
            <UploadPanel />
          </main>
        )}

        {mode === "audit" && (
          <main className="main-pane">
            <AuditLog entries={auditEntries} />
          </main>
        )}

        {mode === "records" && (
          <main className="main-pane">
            <RecordsView records={customerRecords} />
          </main>
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <I18nProvider locale="en">
      <AppShell />
    </I18nProvider>
  );
}
