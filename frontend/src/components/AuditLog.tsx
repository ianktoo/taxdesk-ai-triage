import { useTranslations } from "../i18n";
import type { AuditEntry } from "../client/apiClient";

export function AuditLog({ entries }: { entries: AuditEntry[] }) {
  const t = useTranslations();
  const sorted = [...entries].reverse();

  return (
    <section aria-labelledby="audit-heading">
      <h1 id="audit-heading" style={{ marginBottom: "var(--space-sm)" }}>
        {t.auditLog.heading}
      </h1>
      <p className="guide-text">{t.auditLog.guide}</p>
      {sorted.length === 0 ? (
        <p className="main-empty">{t.auditLog.empty}</p>
      ) : (
        <div className="table-scroll">
          <table className="audit-table">
            <caption className="sr-only">{t.auditLog.heading}</caption>
            <thead>
              <tr>
                <th scope="col">{t.auditLog.columnTime}</th>
                <th scope="col">{t.auditLog.columnCustomer}</th>
                <th scope="col">{t.auditLog.columnEvent}</th>
                <th scope="col">{t.auditLog.columnDetail}</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((entry, index) => (
                <tr key={`${entry.timestamp}-${index}`}>
                  <td>{new Date(entry.timestamp).toLocaleString()}</td>
                  <td>{entry.persona_id}</td>
                  <td>{entry.event_type}</td>
                  <td>{entry.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
