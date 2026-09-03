import { useId, useRef, useState } from "react";
import { useTranslations } from "../i18n";
import { extractUploadedDocument, type ExtractionResult } from "../client/apiClient";
import { Banner } from "./Banner";
import { FileIcon } from "./icons";
import { Spinner } from "./Spinner";

// Mirrors AUTO_APPROVE_CONFIDENCE_THRESHOLD in api/config/settings.py.
// The backend does not report its threshold, so this is a display-only
// echo of the default: change one and the other must follow.
const CONFIDENCE_THRESHOLD = 0.85;

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(0)}%`;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

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

  // Mirrors the backend's triage rule: any field below the threshold
  // sends the request to a human instead of auto-approving.
  const lowConfidenceFields = result
    ? result.fields.filter((f) => f.confidence < CONFIDENCE_THRESHOLD).map((f) => f.name)
    : [];
  const needsReview =
    result !== null &&
    (lowConfidenceFields.length > 0 || result.document_type_confidence < CONFIDENCE_THRESHOLD);

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
        <div className="upload-result">
          <h4>{t.upload.resultHeading}</h4>

          <div className="doc-preview-card">
            <span className="doc-preview-icon">
              <FileIcon />
            </span>
            <div className="doc-preview-meta">
              <div className="filename">{result.document_type.replace(/_/g, " ")}</div>
              <div className="doctype">
                {t.upload.typeConfidence}: {formatPercent(result.document_type_confidence)}
              </div>
            </div>
          </div>

          <h5>{t.upload.fileHeading}</h5>
          <dl className="meta-grid">
            <dt>{t.upload.fileName}</dt>
            <dd className="mono">{result.source_filename}</dd>
            {selectedFile && (
              <>
                <dt>{t.upload.fileSize}</dt>
                <dd className="mono">{formatBytes(selectedFile.size)}</dd>
                <dt>{t.upload.fileType}</dt>
                <dd className="mono">{selectedFile.type || "—"}</dd>
                <dt>{t.upload.fileModified}</dt>
                <dd className="mono">{new Date(selectedFile.lastModified).toLocaleString()}</dd>
              </>
            )}
          </dl>

          <h5>{t.upload.summaryHeading}</h5>
          <dl className="meta-grid">
            <dt>{t.upload.detectedType}</dt>
            <dd className="mono">{result.document_type}</dd>
            <dt>{t.upload.fieldsFound}</dt>
            <dd className="mono">{result.fields.length}</dd>
            <dt>{t.upload.fieldsLowConfidence}</dt>
            <dd className="mono">{lowConfidenceFields.length}</dd>
            <dt>{t.upload.verdict}</dt>
            <dd>
              <span className={`status-badge ${needsReview ? "review" : "ready"}`}>
                {needsReview ? t.upload.verdictReview : t.upload.verdictAuto}
              </span>
              {needsReview && (
                <span className="guide-text verdict-reason">
                  {t.upload.verdictReviewReason(lowConfidenceFields.join(", ").replace(/_/g, " "))}
                </span>
              )}
            </dd>
          </dl>

          {result.fields.length === 0 ? (
            <p className="main-empty">{t.upload.noFields}</p>
          ) : (
            <div className="table-scroll">
              <table className="field-table">
                <thead>
                  <tr>
                    <th scope="col">{t.upload.columnField}</th>
                    <th scope="col">{t.upload.columnValue}</th>
                    <th scope="col">{t.upload.columnConfidence}</th>
                  </tr>
                </thead>
                <tbody>
                  {result.fields.map((field) => (
                    <tr key={field.name}>
                      <td className="field-name">{field.name.replace(/_/g, " ")}</td>
                      <td>{field.value}</td>
                      <td className={`field-confidence mono ${field.confidence < CONFIDENCE_THRESHOLD ? "low" : ""}`}>
                        {formatPercent(field.confidence)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
