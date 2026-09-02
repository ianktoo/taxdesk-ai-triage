import { useId, useRef, useState } from "react";
import { useTranslations } from "../i18n";
import { extractUploadedDocument, type ExtractionResult } from "../client/apiClient";
import { Banner } from "./Banner";

const CONFIDENCE_THRESHOLD = 0.85;

export function UploadPanel() {
  const t = useTranslations();
  const inputId = useId();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
    setResult(null);
    setError(null);
  }

  function handleRemove() {
    setSelectedFile(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  async function handleAnalyze() {
    if (!selectedFile) return;
    setAnalyzing(true);
    setError(null);

    const response = await extractUploadedDocument(selectedFile);
    setAnalyzing(false);

    if (response.ok) {
      setResult(response.data);
    } else {
      setError(response.error);
    }
  }

  return (
    <section className="card" aria-labelledby="upload-heading">
      <h2 id="upload-heading">{t.upload.heading}</h2>
      <Banner kind="notice">{t.upload.pocNotice}</Banner>
      <p className="guide-text">{t.upload.guide}</p>

      <div className="upload-controls">
        <label htmlFor={inputId} className="upload-label">
          {t.upload.chooseFile}
        </label>
        <input
          ref={fileInputRef}
          id={inputId}
          type="file"
          accept="application/pdf,image/png,image/jpeg"
          onChange={handleFileChange}
        />
        <span className="guide-text">{selectedFile ? selectedFile.name : t.upload.noFileChosen}</span>
      </div>

      <div className="action-row">
        <button
          type="button"
          className="primary"
          disabled={!selectedFile || analyzing}
          aria-busy={analyzing}
          onClick={handleAnalyze}
        >
          {analyzing ? t.upload.analyzing : t.upload.analyzeButton}
        </button>
        {selectedFile && (
          <button type="button" className="danger" disabled={analyzing} onClick={handleRemove}>
            {t.upload.removeButton}
          </button>
        )}
      </div>

      {error && (
        <p role="alert">
          {t.upload.errorPrefix} {error}
        </p>
      )}

      {result && (
        <article className="card">
          <h3>{t.upload.resultHeading}</h3>
          <p>
            <strong>{result.document_type}</strong> (
            {(result.document_type_confidence * 100).toFixed(0)}% confidence)
          </p>
          {result.fields.map((field) => (
            <div className="field-row" key={field.name}>
              <span>{field.name.replace(/_/g, " ")}</span>
              <span>{field.value}</span>
              <span className={`field-confidence ${field.confidence < CONFIDENCE_THRESHOLD ? "low" : ""}`}>
                {(field.confidence * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </article>
      )}
    </section>
  );
}
