/**
 * Thin API client for the InterviewOS backend.
 *
 * One place that knows the base URL and error shape. Feature modules import typed
 * helpers rather than calling `fetch` directly.
 */
import type {
  ConnectionTestResult,
  ProviderMeta,
  ProviderSetting,
  ProviderSettingsUpsert,
  Workspace,
  WorkspaceCreate,
} from "@/lib/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  workspaces: {
    list: () => request<Workspace[]>("/api/workspaces"),
    create: (data: WorkspaceCreate) =>
      request<Workspace>("/api/workspaces", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    remove: (id: string) =>
      request<void>(`/api/workspaces/${id}`, { method: "DELETE" }),
  },
  settings: {
    providers: () => request<ProviderMeta[]>("/api/settings/providers"),
    list: () => request<ProviderSetting[]>("/api/settings"),
    upsert: (data: ProviderSettingsUpsert) =>
      request<ProviderSetting>("/api/settings", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    test: (data: {
      provider: string;
      api_key?: string | null;
      chat_model?: string | null;
      base_url?: string | null;
    }) =>
      request<ConnectionTestResult>("/api/settings/test", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    models: (provider: string) =>
      request<{ models: string[] }>(
        `/api/settings/models?provider=${encodeURIComponent(provider)}`,
      ),
  },
};
