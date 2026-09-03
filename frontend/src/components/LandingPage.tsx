import { useTranslations } from "../i18n";
import { MailIcon, TicketQueueIcon, CheckCircleIcon, ExternalLinkIcon } from "./icons";
import { ThemeToggle } from "./ThemeToggle";
import { SectionNav } from "./SectionNav";

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

  const techStack = [
    { name: t.landing.techStackNutrientName, body: t.landing.techStackNutrientBody },
    { name: t.landing.techStackOpenaiName, body: t.landing.techStackOpenaiBody },
    { name: t.landing.techStackReactName, body: t.landing.techStackReactBody },
    { name: t.landing.techStackFastapiName, body: t.landing.techStackFastapiBody },
    { name: t.landing.techStackUpstashName, body: t.landing.techStackUpstashBody },
    { name: t.landing.techStackVercelName, body: t.landing.techStackVercelBody },
    { name: t.landing.techStackClaudeName, body: t.landing.techStackClaudeBody },
  ];

  const navItems = [
    { id: "problem", label: t.landing.navProblem },
    { id: "how-it-works", label: t.landing.navHowItWorks },
    { id: "use-case", label: t.landing.navUseCase },
    { id: "tech-stack", label: t.landing.navTechStack },
    { id: "about", label: t.landing.navAbout },
  ];

  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="landing-container landing-nav-inner">
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
        </div>
      </header>

      <SectionNav items={navItems} />

      <section className="landing-hero" id="problem">
        <div className="landing-container landing-hero-inner">
          <div className="landing-hero-copy">
            <h1>{t.landing.headline}</h1>
            <p className="landing-subhead">{t.landing.subhead}</p>

            <div className="landing-persona">
              <p>{t.landing.personaBob}</p>
            </div>

            <button type="button" className="primary landing-cta" onClick={onTryDemo}>
              {t.landing.cta}
            </button>
            <p className="landing-poc">{t.app.pocNotice}</p>
          </div>

          <div className="landing-hero-media">
            <img
              src="/illustrations/hero.png"
              alt="Illustration of a support agent wearing a headset, working at a laptop"
              width={2000}
              height={1414}
            />
            <p className="landing-credit">
              Illustration by{" "}
              <a
                href="https://unsplash.com/illustrations/person-working-on-laptop-workspace-IAhkIOun8FM"
                target="_blank"
                rel="noopener noreferrer"
              >
                YuguDesign
              </a>{" "}
              on{" "}
              <a
                href="https://unsplash.com/illustrations/person-working-on-laptop-workspace-IAhkIOun8FM"
                target="_blank"
                rel="noopener noreferrer"
              >
                Unsplash
              </a>
            </p>
          </div>
        </div>
      </section>

      <section className="landing-steps" id="how-it-works" aria-label={t.landing.stepsHeading}>
        <div className="landing-container landing-steps-inner">
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
        </div>
      </section>

      <section className="landing-usecase" id="use-case" aria-label={t.landing.useCaseHeading}>
        <div className="landing-container landing-usecase-inner">
          <h2 className="landing-section-heading">{t.landing.useCaseHeading}</h2>
          <p className="landing-section-guide">{t.landing.useCaseGuide}</p>

          <div className="usecase-mock">
            <div className="usecase-mock-row">
              <span className="usecase-mock-label">{t.landing.useCaseMessageLabel}</span>
              <p className="usecase-mock-message">{t.landing.useCaseMessage}</p>
            </div>
            <div className="usecase-mock-row">
              <span className="usecase-mock-label">{t.landing.useCaseAttachmentsLabel}</span>
              <div className="usecase-mock-chips">
                <span className="attachment-chip">change_of_address_form.pdf</span>
                <span className="attachment-chip">utility_bill.pdf</span>
                <span className="attachment-chip">w2_2025.pdf</span>
                <span className="attachment-chip">state_id_card.pdf</span>
              </div>
            </div>
            <div className="usecase-mock-row">
              <span className="usecase-mock-label">{t.landing.useCaseExtractedLabel}</span>
              <ul className="usecase-mock-list">
                <li>{t.landing.useCaseExtractedAddress}</li>
                <li className="usecase-mock-flagged">{t.landing.useCaseExtractedId}</li>
              </ul>
            </div>
            <div className="usecase-mock-row">
              <span className="usecase-mock-label">{t.landing.useCaseOutcomeLabel}</span>
              <p className="usecase-mock-outcome">
                <span className="status-badge review">{t.queue.statusReview}</span>
                <span>{t.landing.useCaseOutcome}</span>
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-techstack" id="tech-stack" aria-label={t.landing.techStackHeading}>
        <div className="landing-container landing-techstack-inner">
          <h2 className="landing-section-heading">{t.landing.techStackHeading}</h2>
          <p className="landing-section-guide">{t.landing.techStackGuide}</p>
          <ul className="techstack-list">
            {techStack.map((item) => (
              <li key={item.name} className="techstack-item">
                <h3>{item.name}</h3>
                <p>{item.body}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="landing-about" id="about" aria-label={t.landing.aboutHeading}>
        <div className="landing-container landing-about-inner">
          <h2 className="landing-section-heading">{t.landing.aboutHeading}</h2>
          <p className="landing-section-guide">{t.landing.aboutBody}</p>
          <dl className="about-links">
            <div>
              <dt>{t.landing.aboutCreatorLabel}</dt>
              <dd>Ian T.</dd>
            </div>
            <div>
              <dt>{t.landing.aboutGithubLabel}</dt>
              <dd>
                <a href="https://github.com/ianktoo" target="_blank" rel="noopener noreferrer">
                  github.com/ianktoo
                  <ExternalLinkIcon width={14} height={14} />
                </a>
              </dd>
            </div>
            <div>
              <dt>{t.landing.aboutSiteLabel}</dt>
              <dd>
                <a href="https://iantoo.space" target="_blank" rel="noopener noreferrer">
                  iantoo.space
                  <ExternalLinkIcon width={14} height={14} />
                </a>
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="landing-container">
          <p>{t.landing.footer}</p>
        </div>
      </footer>
    </div>
  );
}
