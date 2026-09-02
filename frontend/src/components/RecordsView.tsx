import { useTranslations } from "../i18n";
import type { RecordUpdate } from "../client/apiClient";

export function RecordsView({ records }: { records: Record<string, RecordUpdate> }) {
  const t = useTranslations();
  const entries = Object.entries(records);

  return (
    <section aria-labelledby="records-heading">
      <h1 id="records-heading" style={{ marginBottom: "var(--space-sm)" }}>
        {t.records.heading}
      </h1>
      <p className="guide-text">{t.records.guide}</p>
      {entries.length === 0 ? (
        <p className="main-empty">{t.records.empty}</p>
      ) : (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-md)" }}>
          {entries.map(([customerName, record]) => (
            <div className="record-card" key={customerName}>
              <h3>{customerName}</h3>
              <dl className="record-fields">
                {Object.entries(record.field_updates).map(([field, value]) => (
                  <div key={field} style={{ display: "contents" }}>
                    <dt>{field.replace(/_/g, " ")}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
