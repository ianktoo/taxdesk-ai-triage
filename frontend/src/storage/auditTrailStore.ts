/** Best-effort local persistence for the audit trail.
 *
 * The backend is stateless by design, so the frontend is the system of
 * record. Browser storage is treated as an optional capability: every
 * operation degrades to a no-op when it is unavailable (private
 * browsing, disabled site data, quota exhausted) and the app keeps
 * working from React state alone for the current page load.
 *
 * Only audit entries are persisted. They name which fields changed, not
 * their values, so nothing extracted from a document lands on disk.
 */
import type { AuditEntry } from "../client/apiClient";

const STORAGE_KEY = "taxdesk-audit-trail";

/** Bumped whenever the stored shape changes; mismatches are discarded. */
const SCHEMA_VERSION = 1;

/** Keeps a long-lived demo from growing into the storage quota. */
const MAX_ENTRIES = 200;

interface StoredPayload {
  v: number;
  entries: AuditEntry[];
}

function isAuditEntry(value: unknown): value is AuditEntry {
  if (typeof value !== "object" || value === null) return false;
  const entry = value as Record<string, unknown>;
  return (
    typeof entry.timestamp === "string" &&
    typeof entry.persona_id === "string" &&
    typeof entry.event_type === "string" &&
    typeof entry.detail === "string"
  );
}

/** Reads persisted entries, discarding anything malformed or stale. */
export function loadAuditTrail(): AuditEntry[] {
  let raw: string | null;
  try {
    raw = window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return [];
  }
  if (!raw) return [];

  try {
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return [];

    const payload = parsed as Partial<StoredPayload>;
    if (payload.v !== SCHEMA_VERSION || !Array.isArray(payload.entries)) return [];

    // A single bad entry discards the batch rather than rendering a
    // half-broken trail: an audit log that silently drops rows is worse
    // than one that starts empty.
    if (!payload.entries.every(isAuditEntry)) return [];

    return payload.entries.slice(-MAX_ENTRIES);
  } catch {
    return [];
  }
}

/** Persists entries, silently doing nothing when storage is unavailable. */
export function saveAuditTrail(entries: AuditEntry[]): void {
  const payload: StoredPayload = {
    v: SCHEMA_VERSION,
    entries: entries.slice(-MAX_ENTRIES),
  };
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // Quota exceeded or storage unavailable. The in-memory trail is
    // unaffected, so the current session still shows every event.
  }
}

export function clearAuditTrail(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nothing to do: if we cannot write, there is nothing stored to clear.
  }
}
