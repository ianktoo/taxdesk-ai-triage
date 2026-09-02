import { useMemo, useState } from "react";
import { useTranslations } from "../i18n";
import type { TriageResult } from "../client/apiClient";

interface Props {
  result: TriageResult;
  onDecision: (decision: "approve" | "correct" | "reject", fieldUpdates: Record<string, string>) => void;
  submitting: boolean;
}

export function ReviewScreen({ result, onDecision, submitting }: Props) {
  const t = useTranslations();

  const initialValues = useMemo(() => {
    const values: Record<string, string> = {};
    for (const attachment of result.attachments) {
      for (const field of attachment.extraction.fields) {
        values[field.name] = field.value;
      }
    }
    return values;
  }, [result]);

  const [editedValues, setEditedValues] = useState(initialValues);

  function updateField(name: string, value: string) {
    setEditedValues((prev) => ({ ...prev, [name]: value }));
  }

  return (
    <section className="card" aria-labelledby="review-heading">
      <h2 id="review-heading">{t.review.heading}</h2>

      {result.attachments.map((attachment) => (
        <article key={attachment.filename} className="card">
          <h3>
            {t.review.attachmentHeading}: {attachment.filename} ({attachment.extraction.document_type})
          </h3>
          <h4>{t.review.extractedFieldsHeading}</h4>
          {attachment.extraction.fields.map((field) => {
            const isLow = attachment.low_confidence_fields.includes(field.name);
            const inputId = `${attachment.filename}-${field.name}`;
            return (
              <div className="field-row" key={field.name}>
                <label htmlFor={inputId}>{field.name.replace(/_/g, " ")}</label>
                <input
                  id={inputId}
                  type="text"
                  value={editedValues[field.name] ?? field.value}
                  onChange={(event) => updateField(field.name, event.target.value)}
                  aria-describedby={`${inputId}-confidence`}
                />
                <span
                  id={`${inputId}-confidence`}
                  className={`field-confidence ${isLow ? "low" : ""}`}
                >
                  {t.review.confidenceLabel}: {(field.confidence * 100).toFixed(0)}%
                </span>
              </div>
            );
          })}
        </article>
      ))}

      <div className="action-row">
        <button
          type="button"
          className="primary"
          disabled={submitting}
          onClick={() => onDecision("approve", editedValues)}
        >
          {t.review.approve}
        </button>
        <button
          type="button"
          disabled={submitting}
          onClick={() => onDecision("correct", editedValues)}
        >
          {t.review.correct}
        </button>
        <button
          type="button"
          className="danger"
          disabled={submitting}
          onClick={() => onDecision("reject", {})}
        >
          {t.review.reject}
        </button>
      </div>
    </section>
  );
}
