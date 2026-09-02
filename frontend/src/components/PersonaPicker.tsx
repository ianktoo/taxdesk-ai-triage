import { useTranslations } from "../i18n";
import type { PersonaSummary } from "../client/apiClient";

interface Props {
  personas: PersonaSummary[];
  onSend: (personaId: string) => void;
  sendingPersonaId: string | null;
}

export function PersonaPicker({ personas, onSend, sendingPersonaId }: Props) {
  const t = useTranslations();

  return (
    <section className="card" aria-labelledby="persona-heading">
      <h2 id="persona-heading">{t.personas.heading}</h2>
      <ul className="persona-list">
        {personas.map((persona) => (
          <li key={persona.id} className="card persona-card">
            <h3>{persona.display_name}</h3>
            <p>{persona.message}</p>
            <p>
              <strong>{t.personas.attachmentsLabel}:</strong>{" "}
              {persona.attachments.join(", ")}
            </p>
            <button
              className="primary"
              type="button"
              onClick={() => onSend(persona.id)}
              disabled={sendingPersonaId === persona.id}
            >
              {t.personas.sendButton}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
