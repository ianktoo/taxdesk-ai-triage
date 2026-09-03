import { useEffect, useState } from "react";
import { useTranslations } from "../i18n";
import {
  generatePersona,
  listSampleDocuments,
  runCustomTriage,
  type TriageResult,
} from "../client/apiClient";
import { Banner } from "./Banner";
import { SendIcon, SparkleIcon } from "./icons";

interface Props {
  onSent: (customerName: string, message: string, result: TriageResult) => void;
}

export function NewRequestPanel({ onSent }: Props) {
  const t = useTranslations();

  const [availableDocs, setAvailableDocs] = useState<string[]>([]);
  const [docsError, setDocsError] = useState<string | null>(null);

  const [scenario, setScenario] = useState("");
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  const [displayName, setDisplayName] = useState("");
  const [message, setMessage] = useState("");
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);

  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);

  useEffect(() => {
    listSampleDocuments().then((result) => {
      if (result.ok) {
        setAvailableDocs(result.data);
      } else {
        setDocsError(result.error);
      }
    });
  }, []);

  async function handleGenerate() {
    if (!scenario.trim()) return;
    setGenerating(true);
    setGenerateError(null);

    const result = await generatePersona(scenario);
    setGenerating(false);

    if (result.ok) {
      setDisplayName(result.data.display_name);
      setMessage(result.data.message);
    } else {
      setGenerateError(result.error);
    }
  }

  function toggleDoc(filename: string) {
    setSelectedDocs((prev) =>
      prev.includes(filename) ? prev.filter((f) => f !== filename) : [...prev, filename],
    );
  }

  async function handleSend() {
    if (!displayName.trim() || !message.trim()) return;
    setSending(true);
    setSendError(null);

    const result = await runCustomTriage({
      customer_name: displayName.trim(),
      message: message.trim(),
      attachments: selectedDocs,
    });

    setSending(false);

    if (result.ok) {
      onSent(displayName.trim(), message.trim(), result.data);
      setScenario("");
      setDisplayName("");
      setMessage("");
      setSelectedDocs([]);
    } else {
      setSendError(result.error);
    }
  }

  return (
    <article>
      <h1 style={{ marginBottom: "var(--space-xs)" }}>{t.newRequest.heading}</h1>
      <p className="guide-text">{t.newRequest.guide}</p>

      <h4>{t.newRequest.scenarioLabel}</h4>
      <textarea
        className="scenario-input"
        rows={3}
        value={scenario}
        onChange={(event) => setScenario(event.target.value)}
        placeholder={t.newRequest.scenarioPlaceholder}
      />
      <div className="action-row" style={{ marginTop: "var(--space-sm)", marginBottom: "var(--space-md)" }}>
        <button type="button" className="primary" disabled={!scenario.trim() || generating} onClick={handleGenerate}>
          <SparkleIcon width={14} height={14} />
          {generating ? t.newRequest.generating : t.newRequest.generateButton}
        </button>
      </div>

      {generateError && (
        <Banner kind="error">
          {t.newRequest.generateErrorPrefix} {generateError}
        </Banner>
      )}

      {(displayName || message) && (
        <>
          <h4>{t.newRequest.nameLabel}</h4>
          <input
            className="scenario-input"
            type="text"
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
          />

          <h4>{t.newRequest.messageLabel}</h4>
          <textarea
            className="scenario-input"
            rows={4}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
          />

          <h4>{t.newRequest.attachmentsLabel}</h4>
          {docsError && <Banner kind="error">{docsError}</Banner>}
          <div className="doc-checkbox-list">
            {availableDocs.map((filename) => (
              <label key={filename} className="doc-checkbox">
                <input
                  type="checkbox"
                  checked={selectedDocs.includes(filename)}
                  onChange={() => toggleDoc(filename)}
                />
                {filename}
              </label>
            ))}
          </div>

          {sendError && (
            <Banner kind="error">
              {t.newRequest.sendErrorPrefix} {sendError}
            </Banner>
          )}

          <div className="action-row" style={{ marginTop: "var(--space-md)" }}>
            <button
              type="button"
              className="primary"
              disabled={!displayName.trim() || !message.trim() || sending}
              aria-busy={sending}
              onClick={handleSend}
            >
              <SendIcon width={14} height={14} />
              {sending ? t.message.sending : t.newRequest.sendButton}
            </button>
          </div>
        </>
      )}
    </article>
  );
}
