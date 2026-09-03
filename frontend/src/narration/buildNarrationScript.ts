/** Builds the text read aloud for a customer request.
 *
 * The spoken version covers what a sighted user gets from the whole
 * pane, not just the message body: the attachment chips are part of the
 * request, so the narration names them too. All wording comes from the
 * locale file; this module only decides the ordering and shape.
 */
import type { TranslationKeys } from "../i18n/en";

/** Turns "change_of_address_form.pdf" into "change of address form".
 *
 * Only a fallback for filenames the locale file has no label for, since
 * AI-generated personas can attach any sample document.
 */
function humanizeFilename(filename: string): string {
  const stem = filename.replace(/\.[^.]+$/, "");
  return stem.replace(/[_-]+/g, " ").trim();
}

function labelFor(filename: string, t: TranslationKeys): string {
  const stem = filename.replace(/\.[^.]+$/, "");
  return t.documentLabels[stem] ?? humanizeFilename(filename);
}

/** Joins labels into a spoken list ("a, b, and c") for the locale. */
function formatList(items: string[], locale: string): string {
  // Intl.ListFormat is supported everywhere this demo runs; the manual
  // join is only a guard for older engines.
  if (typeof Intl.ListFormat === "function") {
    return new Intl.ListFormat(locale, { style: "long", type: "conjunction" }).format(items);
  }
  return items.join(", ");
}

export function buildNarrationScript(
  message: string,
  attachments: string[],
  t: TranslationKeys,
  locale = "en",
): string {
  if (attachments.length === 0) {
    return `${message} ${t.narration.noAttachments}`.trim();
  }

  const labels = attachments.map((filename) => labelFor(filename, t));
  const summary = t.narration.attachmentSummary(attachments.length, formatList(labels, locale));

  return `${message} ${summary}`.trim();
}
