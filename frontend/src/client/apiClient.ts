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
}

export function runTriage(personaId: string) {
  return request<TriageResult>(`/triage/${personaId}`, { method: "POST" });
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
}

export function submitApproval(body: {
  persona_id: string;
  customer_name: string;
  request_category: string;
  decision: "approve" | "correct" | "reject";
  field_updates: Record<string, string>;
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
