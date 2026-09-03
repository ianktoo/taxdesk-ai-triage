import { useTranslations } from "../i18n";
import { MailIcon, TicketQueueIcon, CheckCircleIcon } from "./icons";
import { ThemeToggle } from "./ThemeToggle";

interface Props {
  onTryDemo: () => void;
}

export function LandingPage({ onTryDemo }: Props) {
  const t = useTranslations();

  const steps = [
    { icon: MailIcon, title: t.landing.step1Title, body: t.landing.step1Body },
    { icon: TicketQueueIcon, title: t.landing.step2Title, body: t.landing.step2Body },
    { icon: CheckCircleIcon, title: t.landing.step3Title, body: t.landing.step3Body },
  ];

  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <span>{t.app.title}</span>
        </div>
        <div className="landing-nav-actions">
          <ThemeToggle />
          <button type="button" className="primary" onClick={onTryDemo}>
            {t.landing.cta}
          </button>
        </div>
      </header>

      <section className="landing-hero">
        <h1>{t.landing.headline}</h1>
        <p className="landing-subhead">{t.landing.subhead}</p>
        <button type="button" className="primary landing-cta" onClick={onTryDemo}>
          {t.landing.cta}
        </button>
        <p className="landing-poc">{t.app.pocNotice}</p>
      </section>

      <section className="landing-steps" aria-label={t.landing.stepsHeading}>
        <h2 className="landing-steps-heading">{t.landing.stepsHeading}</h2>
        <ol className="landing-step-list">
          {steps.map((step, index) => (
            <li key={step.title} className="landing-step">
              <span className="landing-step-number mono">{String(index + 1).padStart(2, "0")}</span>
              <step.icon width={22} height={22} />
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <footer className="landing-footer">
        <p>{t.landing.footer}</p>
      </footer>
    </div>
  );
}
