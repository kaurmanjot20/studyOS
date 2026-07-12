export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  subject: string | null;
  color: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceCreate {
  name: string;
  description?: string | null;
  subject?: string | null;
  color?: string | null;
}

export type DocumentStatus = "queued" | "processing" | "ready" | "failed";

export interface DocumentItem {
  id: string;
  workspace_id: string;
  filename: string;
  content_type: string | null;
  size_bytes: number;
  status: DocumentStatus;
  error: string | null;
  title: string | null;
  page_count: number | null;
  word_count: number | null;
  chunk_count: number;
  embedding_model: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProviderMeta {
  name: string;
  label: string;
  requires_api_key: boolean;
  supports_embeddings: boolean;
  default_base_url: string | null;
}

export interface ProviderSetting {
  provider: string;
  chat_model: string | null;
  embedding_model: string | null;
  base_url: string | null;
  is_active: boolean;
  has_api_key: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProviderSettingsUpsert {
  provider: string;
  api_key?: string | null;
  chat_model?: string | null;
  embedding_model?: string | null;
  base_url?: string | null;
  set_active?: boolean;
}

export interface ConnectionTestResult {
  ok: boolean;
  detail: string;
  models_available: number | null;
}
