import { useTranslations } from "../i18n";
import type { AuditEntry } from "../client/apiClient";

export function AuditLog({ entries }: { entries: AuditEntry[] }) {
  const t = useTranslations();

  return (
    <section className="card" aria-labelledby="audit-heading">
      <h2 id="audit-heading">{t.auditLog.heading}</h2>
      {entries.length === 0 ? (
        <p>{t.auditLog.empty}</p>
      ) : (
        <table className="audit-table">
          <caption className="sr-only">{t.auditLog.heading}</caption>
          <thead>
            <tr>
              <th scope="col">{t.auditLog.columnTime}</th>
              <th scope="col">{t.auditLog.columnPersona}</th>
              <th scope="col">{t.auditLog.columnEvent}</th>
              <th scope="col">{t.auditLog.columnDetail}</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry, index) => (
              <tr key={`${entry.timestamp}-${index}`}>
                <td>{new Date(entry.timestamp).toLocaleString()}</td>
                <td>{entry.persona_id}</td>
                <td>{entry.event_type}</td>
                <td>{entry.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
