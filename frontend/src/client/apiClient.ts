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

export interface PersonaSummary {
  id: string;
  display_name: string;
  message: string;
  attachments: string[];
}

export function listPersonas() {
  return request<PersonaSummary[]>("/personas");
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
