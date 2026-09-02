import { useTranslations } from "../i18n";
import type { RecordUpdate } from "../client/apiClient";

export function CustomerRecordView({ records }: { records: Record<string, RecordUpdate> }) {
  const t = useTranslations();
  const entries = Object.entries(records);

  return (
    <section className="card" aria-labelledby="record-heading">
      <h2 id="record-heading">{t.customerRecord.heading}</h2>
      <p className="guide-text">{t.customerRecord.guide}</p>
      {entries.length === 0 ? (
        <p>{t.customerRecord.empty}</p>
      ) : (
        entries.map(([customerName, record]) => (
          <article key={customerName} className="card">
            <h3>{customerName}</h3>
            <ul>
              {Object.entries(record.field_updates).map(([field, value]) => (
                <li key={field}>
                  <strong>{field.replace(/_/g, " ")}:</strong> {value}
                </li>
              ))}
            </ul>
          </article>
        ))
      )}
    </section>
  );
}
