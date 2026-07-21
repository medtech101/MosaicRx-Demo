const BASE = "/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: options.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface DocumentOut {
  id: number;
  original_filename: string;
  doc_type: string;
  status: string;
  unit_count: number;
  created_at: string;
}

export interface RedactionEntryOut {
  id: number;
  location: string;
  category: string;
  original_text: string;
  replacement_text: string;
  status: string;
}

export interface ImageFlagOut {
  id: number;
  location: string;
  reason: string;
  ocr_text: string | null;
  matched_terms: string[] | null;
  action: string;
  thumbnail_path: string | null;
}

export interface DocumentReviewOut {
  document: DocumentOut;
  redactions: RedactionEntryOut[];
  image_flags: ImageFlagOut[];
  sanitized_markdown_preview: string;
}

export interface BlocklistTerm {
  id: number;
  term: string;
  category: string;
}

export const api = {
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentOut>("/documents/upload", { method: "POST", body: form });
  },
  listDocuments: () => request<DocumentOut[]>("/documents"),
  getReview: (id: number) => request<DocumentReviewOut>(`/documents/${id}/review`),
  confirmDocument: (
    id: number,
    redactionDecisions: { id: number; approve: boolean }[],
    imageDecisions: { id: number; action: string }[]
  ) =>
    request(`/documents/${id}/confirm`, {
      method: "POST",
      body: JSON.stringify({ redaction_decisions: redactionDecisions, image_decisions: imageDecisions }),
    }),
  rejectDocument: (id: number) => request(`/documents/${id}/reject`, { method: "POST" }),
  imageThumbnailUrl: (documentId: number, flagId: number) =>
    `${BASE}/documents/${documentId}/image-flags/${flagId}/thumbnail`,

  listBlocklist: () => request<BlocklistTerm[]>("/settings/blocklist"),
  addBlocklistTerm: (term: string, category: string) =>
    request<BlocklistTerm>("/settings/blocklist", { method: "POST", body: JSON.stringify({ term, category }) }),
  deleteBlocklistTerm: (id: number) => request(`/settings/blocklist/${id}`, { method: "DELETE" }),

  getAppSettings: () => request<Record<string, unknown>>("/settings/app"),
  setAppSetting: (key: string, value: unknown) =>
    request(`/settings/app/${key}`, { method: "PUT", body: JSON.stringify({ value }) }),
};
