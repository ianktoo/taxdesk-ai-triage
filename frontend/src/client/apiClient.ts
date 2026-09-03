import type { ApiResult } from "./apiContract";

// Components never call fetch() directly, only this module, so every
// backend call goes through the {ok,data}/{ok,error} contract.
const BASE_URL = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
    const body = await response.json();
    return body as ApiResult<T>;
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : "Network error" };
  }
}

// GET-able directly by the browser (used as a link href, not fetched
// through request()), so it's exempt from the {ok,data} contract.
export function documentUrl(filename: string): string {
  return `${BASE_URL}/documents/${encodeURIComponent(filename)}`;
}

export interface PersonaSummary {
  id: string;
  display_name: string;
  message: string;
  attachments: string[];
}

export function listPersonas() {
  return request<PersonaSummary[]>("/personas");
}

export function listSampleDocuments() {
  return request<string[]>("/sample-documents");
}

export interface DraftPersona {
  display_name: string;
  message: string;
}

export function generatePersona(scenario: string) {
  return request<DraftPersona>("/personas/generate", {
    method: "POST",
    body: JSON.stringify({ scenario }),
  });
}

export function runCustomTriage(body: { customer_name: string; message: string; attachments: string[] }) {
  return request<TriageResult>("/triage/custom", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export interface ExtractedField {
  name: string;
  value: string;
  confidence: number;
}

export interface ExtractionResult {
  document_type: string;
  document_type_confidence: number;
  fields: ExtractedField[];
  source_filename: string;
}

export interface AttachmentResult {
  filename: string;
  extraction: ExtractionResult;
  low_confidence_fields: string[];
}

/** One observable action from the orchestrated run.
 *
 * Mirrors AgentStep in api/integrations/reasoning/base.py. An empty
 * `model` means the step was deterministic and never called one.
 */
export interface AgentStep {
  index: number;
  agent: string;
  action: "delegate" | "tool_call" | "reason" | "decide";
  status: "ok" | "error" | "fallback" | "skipped";
  detail: string;
  duration_ms: number;
  model: string;
}

export interface FieldObservation {
  filename: string;
  value: string;
}

export interface FieldAgreement {
  field: string;
  value: string;
  filenames: string[];
}

export interface FieldConflict {
  field: string;
  note: string;
  observations: FieldObservation[];
}

export interface TriageResult {
  persona_id: string;
  customer_name: string;
  message: string;
  request_category: string;
  request_category_label: string;
  summary: string;
  status: "ready_to_auto_approve" | "needs_human_review";
  review_reasons: string[];
  attachments: AttachmentResult[];
  agent_trace: AgentStep[];
  agreements: FieldAgreement[];
  conflicts: FieldConflict[];
  /** A proposal for the reviewer to approve or edit. Never sent by the system. */
  draft_response: string;
  classifier_rationale: string;
  reasoner_model: string;
}

export function runTriage(personaId: string) {
  return request<TriageResult>(`/triage/${personaId}`, { method: "POST" });
}

/** Splits an SSE byte stream into (event, data) pairs.
 *
 * Frames are separated by a blank line and can be split across network
 * chunks, so the tail of a read is held back until its terminating
 * blank line arrives.
 */
async function* readSseFrames(body: ReadableStream<Uint8Array>) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let split = buffer.indexOf("\n\n");
      while (split !== -1) {
        const frame = buffer.slice(0, split);
        buffer = buffer.slice(split + 2);
        split = buffer.indexOf("\n\n");

        let event = "";
        let data = "";
        for (const line of frame.split("\n")) {
          if (line.startsWith("event: ")) event = line.slice(7);
          else if (line.startsWith("data: ")) data = line.slice(6);
        }
        if (event && data) yield { event, data };
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/** Runs triage over SSE, reporting each agent step as it happens.
 *
 * The terminal event carries the same {ok,data}/{ok,error} envelope the
 * non-streaming route returns, so the resolved value here is identical
 * either way. If streaming is unavailable for any reason — an old
 * browser, a proxy that buffers or rejects the stream — this falls back
 * to the plain endpoint and the caller simply sees no steps.
 */
export async function streamTriage(
  path: string,
  body: unknown,
  onStep: (step: AgentStep) => void,
  fallback: () => Promise<ApiResult<TriageResult>>,
): Promise<ApiResult<TriageResult>> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    return fallback();
  }

  if (!response.ok || !response.body) return fallback();

  let terminal: ApiResult<TriageResult> | null = null;
  try {
    for await (const frame of readSseFrames(response.body)) {
      const payload = JSON.parse(frame.data);
      if (frame.event === "step") {
        onStep(payload as AgentStep);
      } else if (frame.event === "result" || frame.event === "error") {
        terminal = payload as ApiResult<TriageResult>;
      }
    }
  } catch (error) {
    // The stream broke partway. Steps already shown stay on screen, but
    // there is no result, so re-run through the non-streaming route
    // rather than reporting a half-finished run as a failure.
    if (!terminal) return fallback();
    return { ok: false, error: error instanceof Error ? error.message : "Stream error" };
  }

  // A stream that ended without a terminal event told us nothing
  // conclusive; the plain route is the source of truth.
  return terminal ?? (await fallback());
}

export function streamPersonaTriage(personaId: string, onStep: (step: AgentStep) => void) {
  return streamTriage(`/triage/${personaId}/stream`, undefined, onStep, () => runTriage(personaId));
}

export function streamCustomTriage(
  body: { customer_name: string; message: string; attachments: string[] },
  onStep: (step: AgentStep) => void,
) {
  return streamTriage(`/triage/custom/stream`, body, onStep, () => runCustomTriage(body));
}

export interface RecordUpdate {
  customer_name: string;
  field_updates: Record<string, string>;
}

export interface AuditEntry {
  timestamp: string;
  persona_id: string;
  event_type: string;
  detail: string;
}

export interface ApprovalResponse {
  record: RecordUpdate | null;
  audit_entry: AuditEntry;
  /** Reply drafted for the decision just made. A proposal, never sent. */
  draft_response: string;
  /** Set when the draft could not be produced; the decision still stands. */
  draft_error: string;
  agent_trace: AgentStep[];
}

export function submitApproval(body: {
  persona_id: string;
  customer_name: string;
  request_category: string;
  request_category_label: string;
  decision: "approve" | "correct" | "reject";
  field_updates: Record<string, string>;
  reason: string;
  corrected_fields: string[];
}) {
  return request<ApprovalResponse>("/approve", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function synthesizeSpeech(text: string): Promise<ApiResult<{ url: string }>> {
  // /speech returns raw audio bytes (not the {ok,data} JSON envelope) on
  // success, but still returns the JSON contract on a rate-limit/error
  // response, so the content-type decides how to parse the body.
  try {
    const response = await fetch(`${BASE_URL}/speech`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.startsWith("audio/")) {
      const blob = await response.blob();
      return { ok: true, data: { url: URL.createObjectURL(blob) } };
    }
    return (await response.json()) as ApiResult<{ url: string }>;
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : "Network error" };
  }
}

export async function extractUploadedDocument(file: File): Promise<ApiResult<ExtractionResult>> {
  // Uses fetch directly (not the shared request() helper) so the browser
  // sets the multipart Content-Type boundary itself.
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${BASE_URL}/extract`, { method: "POST", body: formData });
    return (await response.json()) as ApiResult<ExtractionResult>;
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : "Network error" };
  }
}
