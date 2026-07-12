/**
 * Thin API client for the InterviewOS backend.
 *
 * One place that knows the base URL and error shape. Feature modules import typed
 * helpers rather than calling `fetch` directly.
 */
import type {
  ConnectionTestResult,
  DocumentItem,
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
  documents: {
    list: (workspaceId: string) =>
      request<DocumentItem[]>(`/api/workspaces/${workspaceId}/documents`),
    get: (id: string) => request<DocumentItem>(`/api/documents/${id}`),
    remove: (id: string) =>
      request<void>(`/api/documents/${id}`, { method: "DELETE" }),
    // Upload uses XHR (not fetch) to report progress events.
    upload: (
      workspaceId: string,
      file: File,
      onProgress?: (percent: number) => void,
    ) =>
      new Promise<DocumentItem>((resolve, reject) => {
        const form = new FormData();
        form.append("file", file);
        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${BASE_URL}/api/workspaces/${workspaceId}/documents`);
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable && onProgress) {
            onProgress(Math.round((e.loaded / e.total) * 100));
          }
        };
        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText) as DocumentItem);
          } else {
            let detail = xhr.statusText;
            try {
              detail = JSON.parse(xhr.responseText).detail ?? detail;
            } catch {
              /* non-JSON */
            }
            reject(new ApiError(xhr.status, detail));
          }
        };
        xhr.onerror = () => reject(new ApiError(0, "Network error"));
        xhr.send(form);
      }),
  },
};
