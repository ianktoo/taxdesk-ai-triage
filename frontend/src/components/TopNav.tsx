import { useTranslations } from "../i18n";
import { ThemeToggle } from "./ThemeToggle";
import type { Mode } from "../App";

interface Props {
  mode: Mode;
  onModeChange: (mode: Mode) => void;
  pendingCount: number;
  onBrandClick: () => void;
}

export function TopNav({ mode, onModeChange, pendingCount, onBrandClick }: Props) {
  const t = useTranslations();

  const items: Array<{ id: Mode; label: string; badge?: number }> = [
    { id: "customer", label: t.nav.customer },
    { id: "agent", label: t.nav.agent, badge: pendingCount || undefined },
    { id: "upload", label: t.nav.upload },
    { id: "audit", label: t.nav.audit },
    { id: "records", label: t.nav.records },
  ];

  return (
    <header className="topbar">
      <button type="button" className="brand" onClick={onBrandClick}>
        <span className="brand-mark" aria-hidden="true" />
        <span className="brand-name">{t.app.title}</span>
      </button>
      <nav className="mode-tabs" aria-label="Sections">
        {items.map(({ id, label, badge }) => (
          <button
            key={id}
            type="button"
            aria-current={mode === id ? "page" : undefined}
            onClick={() => onModeChange(id)}
          >
            {label}
            {badge ? <span className="mono"> ({badge})</span> : null}
          </button>
        ))}
      </nav>
      <span className="poc-chip">{t.app.pocNotice}</span>
      <ThemeToggle />
    </header>
  );
}
