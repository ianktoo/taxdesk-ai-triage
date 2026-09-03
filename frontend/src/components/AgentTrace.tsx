import { useTranslations } from "../i18n";
import type { AgentStep } from "../client/apiClient";

/** Renders the ordered record of what happened during one triage run.
 *
 * An ordered list, because the steps are a sequence and their order is
 * the information: reading it top to bottom is reading what the system
 * did. Each step names the agent, what kind of action it was, and
 * whether a model was involved, so a reviewer can tell a real inference
 * apart from a deterministic rule at a glance.
 */
interface Props {
  steps: AgentStep[];
  /** True while the run is still streaming, so the list is growing. */
  live?: boolean;
}

export function AgentTrace({ steps, live = false }: Props) {
  const t = useTranslations();

  if (steps.length === 0) {
    return <p className="guide-text">{live ? t.trace.waiting : t.trace.empty}</p>;
  }

  return (
    <div>
      <h4>{live ? t.trace.liveHeading : t.trace.heading}</h4>
      <p className="guide-text">{live ? t.trace.liveGuide : t.trace.guide}</p>

      {/* Announces newly arriving steps to screen readers without
          stealing focus. Polite, since the run is not interactive. */}
      <ol className="trace-list" aria-live={live ? "polite" : undefined} aria-busy={live}>
        {steps.map((step, position) => (
          <li
            key={step.index}
            className={`trace-step ${step.status}${live && position === steps.length - 1 ? " latest" : ""}`}
          >
            <div className="trace-step-head">
              <span className="trace-agent">{t.trace.agents[step.agent] ?? step.agent}</span>
              <span className="trace-action">{t.trace.actions[step.action] ?? step.action}</span>
              {step.status !== "ok" && (
                <span className={`trace-status ${step.status}`}>
                  {t.trace.statuses[step.status] ?? step.status}
                </span>
              )}
              <span className="trace-meta mono">
                {step.model || t.trace.deterministic}
                {step.duration_ms > 0 && ` · ${t.trace.durationLabel(step.duration_ms)}`}
              </span>
            </div>
            <p className="trace-detail">{step.detail}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}
