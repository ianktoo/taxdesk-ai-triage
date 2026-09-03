import { useId, useRef, useState } from "react";
import { useTranslations } from "../i18n";
import { extractUploadedDocument, type ExtractionResult } from "../client/apiClient";
import { Banner } from "./Banner";
import { FileIcon } from "./icons";
import { Spinner } from "./Spinner";

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
    <section aria-labelledby="upload-heading">
      <h1 id="upload-heading" style={{ marginBottom: "var(--space-sm)" }}>
        {t.upload.heading}
      </h1>
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
        <span className="guide-text" style={{ margin: 0 }}>
          {selectedFile ? selectedFile.name : t.upload.noFileChosen}
        </span>
      </div>

      <div className="action-row">
        <button
          type="button"
          className="primary"
          disabled={!selectedFile || analyzing}
          aria-busy={analyzing}
          onClick={handleAnalyze}
        >
          {analyzing && <Spinner />} {analyzing ? t.upload.analyzing : t.upload.analyzeButton}
        </button>
        {selectedFile && (
          <button type="button" className="danger" disabled={analyzing} onClick={handleRemove}>
            {t.upload.removeButton}
          </button>
        )}
      </div>

      {error && (
        <p role="alert" className="banner error" style={{ marginTop: "var(--space-md)" }}>
          {t.upload.errorPrefix} {error}
        </p>
      )}

      {result && (
        <div style={{ marginTop: "var(--space-lg)" }}>
          <h4>{t.upload.resultHeading}</h4>
          <div className="doc-preview-card">
            <span className="doc-preview-icon">
              <FileIcon />
            </span>
            <div className="doc-preview-meta">
              <div className="filename">{result.document_type}</div>
              <div className="doctype">{(result.document_type_confidence * 100).toFixed(0)}% confidence</div>
            </div>
          </div>
          <table className="field-table">
            <thead>
              <tr>
                <th scope="col">Field</th>
                <th scope="col">Value</th>
                <th scope="col">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {result.fields.map((field) => (
                <tr key={field.name}>
                  <td className="field-name">{field.name.replace(/_/g, " ")}</td>
                  <td>{field.value}</td>
                  <td className={`field-confidence mono ${field.confidence < CONFIDENCE_THRESHOLD ? "low" : ""}`}>
                    {(field.confidence * 100).toFixed(0)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
