import { useTranslations } from "../i18n";
import { MailIcon, TicketQueueIcon, UploadIcon, AuditIcon, RecordsIcon } from "./icons";
import type { Mode } from "../App";

interface Props {
  mode: Mode;
  onModeChange: (mode: Mode) => void;
  pendingCount: number;
  onBrandClick: () => void;
}

export function TopNav({ mode, onModeChange, pendingCount, onBrandClick }: Props) {
  const t = useTranslations();

  const items: Array<{ id: Mode; label: string; icon: typeof MailIcon; badge?: number }> = [
    { id: "customer", label: t.nav.customer, icon: MailIcon },
    { id: "agent", label: t.nav.agent, icon: TicketQueueIcon, badge: pendingCount || undefined },
    { id: "upload", label: t.nav.upload, icon: UploadIcon },
    { id: "audit", label: t.nav.audit, icon: AuditIcon },
    { id: "records", label: t.nav.records, icon: RecordsIcon },
  ];

  return (
    <header className="topbar">
      <button type="button" className="brand" onClick={onBrandClick}>
        <span className="brand-mark" aria-hidden="true" />
        <span className="brand-name">{t.app.title}</span>
      </button>
      <nav className="mode-tabs" aria-label="Sections">
        {items.map(({ id, label, icon: Icon, badge }) => (
          <button
            key={id}
            type="button"
            aria-current={mode === id ? "page" : undefined}
            onClick={() => onModeChange(id)}
          >
            <Icon />
            <span className="label">{label}</span>
            {badge ? <span className="mono">({badge})</span> : null}
          </button>
        ))}
      </nav>
      <span className="poc-chip">{t.app.pocNotice}</span>
    </header>
  );
}
