import { useTranslations } from "../i18n";
import { SparkleIcon } from "./icons";
import { Spinner } from "./Spinner";
import type { PersonaSummary } from "../client/apiClient";

interface Props {
  personas: PersonaSummary[];
  loading: boolean;
  selectedPersonaId: string | null;
  creatingNew: boolean;
  onSelect: (personaId: string) => void;
  onStartNew: () => void;
}

export function ContactSidebar({ personas, loading, selectedPersonaId, creatingNew, onSelect, onStartNew }: Props) {
  const t = useTranslations();

  return (
    <aside className="sidebar" aria-label={t.contacts.heading}>
      <div className="sidebar-header">
        <h2>{t.contacts.heading}</h2>
      </div>
      <div className="sidebar-list" style={{ paddingBottom: 0 }}>
        <button type="button" className="sidebar-row new-request-row" aria-current={creatingNew} onClick={onStartNew}>
          <div className="row-title">
            <SparkleIcon width={14} height={14} />
            {t.contacts.newRequest}
          </div>
        </button>
      </div>
      {loading ? (
        <p className="sidebar-empty">
          <Spinner /> {t.contacts.loading}
        </p>
      ) : personas.length === 0 ? (
        <p className="sidebar-empty">{t.contacts.guide}</p>
      ) : (
        <ul className="sidebar-list">
          {personas.map((persona) => (
            <li key={persona.id}>
              <button
                type="button"
                className="sidebar-row"
                aria-current={!creatingNew && selectedPersonaId === persona.id}
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
