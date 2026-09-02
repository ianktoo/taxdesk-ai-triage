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
import { PersonaPicker } from "./components/PersonaPicker";
import { TriageSummary } from "./components/TriageSummary";
import { ReviewScreen } from "./components/ReviewScreen";
import { AuditLog } from "./components/AuditLog";
import { CustomerRecordView } from "./components/CustomerRecordView";

type Tab = "triage" | "audit" | "record";

function AppShell() {
  const t = useTranslations();

  const [personas, setPersonas] = useState<PersonaSummary[]>([]);
  const [sendingPersonaId, setSendingPersonaId] = useState<string | null>(null);
  const [triageResult, setTriageResult] = useState<TriageResult | null>(null);
  const [triageError, setTriageError] = useState<string | null>(null);
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [customerRecords, setCustomerRecords] = useState<Record<string, RecordUpdate>>({});
  const [activeTab, setActiveTab] = useState<Tab>("triage");

  useEffect(() => {
    listPersonas().then((result) => {
      if (result.ok) {
        setPersonas(result.data);
      }
    });
  }, []);

  async function handleSend(personaId: string) {
    setSendingPersonaId(personaId);
    setTriageError(null);
    setTriageResult(null);

    const result = await runTriage(personaId);
    setSendingPersonaId(null);

    if (result.ok) {
      setTriageResult(result.data);
    } else {
      setTriageError(result.error);
    }
  }

  async function handleDecision(
    decision: "approve" | "correct" | "reject",
    fieldUpdates: Record<string, string>,
  ) {
    if (!triageResult) return;
    setSubmittingDecision(true);

    const result = await submitApproval({
      persona_id: triageResult.persona_id,
      customer_name: triageResult.customer_name,
      request_category: triageResult.request_category,
      decision,
      field_updates: decision === "reject" ? {} : fieldUpdates,
    });

    setSubmittingDecision(false);

    if (result.ok) {
      setAuditEntries((prev) => [...prev, result.data.audit_entry]);
      if (result.data.record) {
        setCustomerRecords((prev) => ({
          ...prev,
          [result.data.record!.customer_name]: result.data.record!,
        }));
      }
      setTriageResult(null);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>{t.app.title}</h1>
        <p>{t.app.subtitle}</p>
      </header>

      <nav className="app-nav" aria-label="Sections">
        <button
          type="button"
          aria-current={activeTab === "triage" ? "page" : undefined}
          onClick={() => setActiveTab("triage")}
        >
          {t.nav.triage}
        </button>
        <button
          type="button"
          aria-current={activeTab === "audit" ? "page" : undefined}
          onClick={() => setActiveTab("audit")}
        >
          {t.nav.auditLog}
        </button>
        <button
          type="button"
          aria-current={activeTab === "record" ? "page" : undefined}
          onClick={() => setActiveTab("record")}
        >
          {t.nav.customerRecord}
        </button>
      </nav>

      {activeTab === "triage" && (
        <>
          <PersonaPicker personas={personas} onSend={handleSend} sendingPersonaId={sendingPersonaId} />
          {sendingPersonaId && <p role="status">{t.triage.loading}</p>}
          {triageError && (
            <p role="alert">
              {t.triage.errorPrefix} {triageError}
            </p>
          )}
          {triageResult && (
            <>
              <TriageSummary result={triageResult} />
              <ReviewScreen result={triageResult} onDecision={handleDecision} submitting={submittingDecision} />
            </>
          )}
        </>
      )}

      {activeTab === "audit" && <AuditLog entries={auditEntries} />}
      {activeTab === "record" && <CustomerRecordView records={customerRecords} />}
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
