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

export interface Source {
  index: number;
  kind: "note" | "web";
  snippet: string;
  // note sources
  filename?: string;
  page?: number | null;
  score?: number;
  // web sources
  title?: string;
  url?: string;
}

export interface PlanTrace {
  reasoning: string;
  tools: string[];
  rewritten_query: string;
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
  plan?: PlanTrace | null;
  sources?: Source[];
  streaming?: boolean;
  error?: string | null;
}

export interface ChatSessionRecord {
  id: string;
  workspace_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface MessageRecord {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  sources: Source[] | null;
  plan: PlanTrace | null;
  created_at: string;
}

export interface InterviewTurn {
  question: string;
  topic: string;
  answer?: string;
  score?: number;
  feedback?: string;
}

export interface InterviewSession {
  id: string;
  workspace_id: string;
  company: string | null;
  subject: string | null;
  difficulty: string;
  status: string;
  target_questions: number;
  asked_count: number;
  score: number | null;
  summary: string | null;
  transcript: InterviewTurn[];
  created_at: string;
  updated_at: string;
}

export interface QuizQuestion {
  topic: string;
  question: string;
  options: string[];
  answer_index: number;
  explanation: string;
}

export interface QuizScoreResult {
  correct: number;
  total: number;
  score_pct: number;
  weak_topics_recorded: string[];
}

export interface Flashcard {
  front: string;
  back: string;
}

export interface MemoryItem {
  id: string;
  workspace_id: string;
  kind: "weak_topic" | "preference" | "note";
  topic: string | null;
  content: string;
  weight: number;
  created_at: string;
  updated_at: string;
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

export interface McpServerStatus {
  name: string;
  label: string;
  enabled: boolean;
  requires: string | null;
  connected: boolean;
  tools: string[];
  error: string | null;
}
