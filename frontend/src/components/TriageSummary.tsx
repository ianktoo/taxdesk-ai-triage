import { useTranslations } from "../i18n";
import type { TriageResult } from "../client/apiClient";

export function TriageSummary({ result }: { result: TriageResult }) {
  const t = useTranslations();
  const isReady = result.status === "ready_to_auto_approve";

  return (
    <section className="card" aria-labelledby="triage-heading">
      <h2 id="triage-heading">{t.triage.heading}</h2>
      <p>
        <span className={`status-badge ${isReady ? "ready" : "review"}`}>
          {isReady ? t.triage.statusReady : t.triage.statusReview}
        </span>
      </p>
      <p>
        <strong>{t.triage.categoryLabel}:</strong> {result.request_category_label}
      </p>
      <p>
        <strong>{t.triage.summaryLabel}:</strong> {result.summary}
      </p>
      {!isReady && result.review_reasons.length > 0 && (
        <div>
          <h3>{t.triage.reviewReasonsHeading}</h3>
          <ul>
            {result.review_reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
