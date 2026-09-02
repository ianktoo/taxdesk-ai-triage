import { useTranslations } from "../i18n";
import type { PersonaSummary } from "../client/apiClient";

interface Props {
  personas: PersonaSummary[];
  selectedPersonaId: string | null;
  onSelect: (personaId: string) => void;
}

export function ContactSidebar({ personas, selectedPersonaId, onSelect }: Props) {
  const t = useTranslations();

  return (
    <aside className="sidebar" aria-label={t.contacts.heading}>
      <div className="sidebar-header">
        <h2>{t.contacts.heading}</h2>
      </div>
      {personas.length === 0 ? (
        <p className="sidebar-empty">{t.contacts.guide}</p>
      ) : (
        <ul className="sidebar-list">
          {personas.map((persona) => (
            <li key={persona.id}>
              <button
                type="button"
                className="sidebar-row"
                aria-current={selectedPersonaId === persona.id}
                onClick={() => onSelect(persona.id)}
              >
                <div className="row-title">{persona.display_name}</div>
                <div className="row-subtitle">{persona.attachments.length} attachments</div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
