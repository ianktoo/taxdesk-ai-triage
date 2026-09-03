import { useTranslations } from "../i18n";
import type { AuditEntry } from "../client/apiClient";

export function AuditLog({ entries, onClear }: { entries: AuditEntry[]; onClear: () => void }) {
  const t = useTranslations();
  const sorted = [...entries].reverse();

  return (
    <section aria-labelledby="audit-heading">
      <div className="audit-header">
        <h1 id="audit-heading">{t.auditLog.heading}</h1>
        {sorted.length > 0 && (
          <button type="button" aria-label={t.auditLog.clearLabel} onClick={onClear}>
            {t.auditLog.clear}
          </button>
        )}
      </div>
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
