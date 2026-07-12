"use client";

import * as React from "react";
import { CheckCircle2, Loader2, X, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type {
  ConnectionTestResult,
  ProviderMeta,
  ProviderSetting,
} from "@/lib/types";

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}

interface FormState {
  apiKey: string;
  chatModel: string;
  embeddingModel: string;
  baseUrl: string;
}

const EMPTY_FORM: FormState = {
  apiKey: "",
  chatModel: "",
  embeddingModel: "",
  baseUrl: "",
};

export function SettingsDialog({ open, onClose, onSaved }: SettingsDialogProps) {
  const [providers, setProviders] = React.useState<ProviderMeta[]>([]);
  const [saved, setSaved] = React.useState<ProviderSetting[]>([]);
  const [selected, setSelected] = React.useState<string | null>(null);
  const [form, setForm] = React.useState<FormState>(EMPTY_FORM);
  const [models, setModels] = React.useState<string[]>([]);
  const [testResult, setTestResult] =
    React.useState<ConnectionTestResult | null>(null);
  const [testing, setTesting] = React.useState(false);
  const [fetching, setFetching] = React.useState(false);
  const [saving, setSaving] = React.useState(false);

  const meta = providers.find((p) => p.name === selected) ?? null;
  const savedFor = saved.find((s) => s.provider === selected) ?? null;

  const load = React.useCallback(async () => {
    const [metaList, savedList] = await Promise.all([
      api.settings.providers(),
      api.settings.list(),
    ]);
    setProviders(metaList);
    setSaved(savedList);
    const active = savedList.find((s) => s.is_active);
    setSelected((cur) => cur ?? active?.provider ?? metaList[0]?.name ?? null);
  }, []);

  React.useEffect(() => {
    if (open) {
      load().catch(() => setProviders([]));
    }
  }, [open, load]);

  // Prefill the form whenever the selected provider (or its saved values) change.
  React.useEffect(() => {
    setModels([]);
    setTestResult(null);
    setForm({
      apiKey: "",
      chatModel: savedFor?.chat_model ?? "",
      embeddingModel: savedFor?.embedding_model ?? "",
      baseUrl: savedFor?.base_url ?? meta?.default_base_url ?? "",
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected]);

  React.useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open || !meta) {
    return open ? <Backdrop onClose={onClose}><Loading /></Backdrop> : null;
  }

  const update = (patch: Partial<FormState>) =>
    setForm((f) => ({ ...f, ...patch }));

  const testPayload = () => ({
    provider: meta.name,
    api_key: form.apiKey || null,
    chat_model: form.chatModel || null,
    base_url: form.baseUrl || null,
  });

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      setTestResult(await api.settings.test(testPayload()));
    } catch {
      setTestResult({ ok: false, detail: "Request failed.", models_available: null });
    } finally {
      setTesting(false);
    }
  };

  const handleFetchModels = async () => {
    setFetching(true);
    try {
      // Persist the key first if provided, so listing can authenticate.
      if (form.apiKey || form.baseUrl) {
        await api.settings.upsert({
          provider: meta.name,
          api_key: form.apiKey || undefined,
          base_url: form.baseUrl || undefined,
          set_active: false,
        });
        setForm((f) => ({ ...f, apiKey: "" }));
        await load();
      }
      const res = await api.settings.models(meta.name);
      setModels(res.models);
    } catch {
      setModels([]);
    } finally {
      setFetching(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.settings.upsert({
        provider: meta.name,
        api_key: form.apiKey || undefined,
        chat_model: form.chatModel || null,
        embedding_model: form.embeddingModel || null,
        base_url: form.baseUrl || null,
        set_active: true,
      });
      await load();
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Backdrop onClose={onClose}>
      <div className="flex max-h-[80vh] w-full max-w-2xl flex-col overflow-hidden rounded-lg border border-border bg-popover shadow-xl">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="text-sm font-semibold">AI Provider Settings</h2>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close">
            <X className="size-4" />
          </Button>
        </div>

        <div className="flex min-h-0 flex-1">
          {/* Provider rail */}
          <div className="w-40 shrink-0 space-y-0.5 border-r border-border p-2">
            {providers.map((p) => {
              const isActive = saved.find(
                (s) => s.provider === p.name && s.is_active,
              );
              return (
                <button
                  key={p.name}
                  onClick={() => setSelected(p.name)}
                  className={cn(
                    "flex w-full items-center justify-between rounded-md px-2 py-1.5 text-sm",
                    p.name === selected
                      ? "bg-secondary text-foreground"
                      : "text-muted-foreground hover:bg-secondary/60",
                  )}
                >
                  <span className="truncate">{p.label}</span>
                  {isActive && <span className="size-1.5 rounded-full bg-accent" />}
                </button>
              );
            })}
          </div>

          {/* Form */}
          <div className="min-w-0 flex-1 space-y-4 overflow-y-auto p-4">
            {meta.requires_api_key && (
              <Field label="API key">
                <Input
                  type="password"
                  value={form.apiKey}
                  onChange={(e) => update({ apiKey: e.target.value })}
                  placeholder={
                    savedFor?.has_api_key
                      ? "•••••••• saved — leave blank to keep"
                      : "Paste your API key"
                  }
                />
              </Field>
            )}

            {meta.default_base_url && (
              <Field label="Base URL">
                <Input
                  value={form.baseUrl}
                  onChange={(e) => update({ baseUrl: e.target.value })}
                  placeholder={meta.default_base_url}
                />
              </Field>
            )}

            <Field label="Chat model">
              <div className="flex gap-2">
                <Input
                  value={form.chatModel}
                  onChange={(e) => update({ chatModel: e.target.value })}
                  placeholder="e.g. gpt-4o-mini"
                  list="chat-models"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleFetchModels}
                  disabled={fetching}
                >
                  {fetching ? <Loader2 className="size-3.5 animate-spin" /> : "Fetch"}
                </Button>
              </div>
              {models.length > 0 && (
                <datalist id="chat-models">
                  {models.map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
              )}
            </Field>

            {meta.supports_embeddings && (
              <Field label="Embedding model">
                <Input
                  value={form.embeddingModel}
                  onChange={(e) => update({ embeddingModel: e.target.value })}
                  placeholder="e.g. text-embedding-3-small"
                />
              </Field>
            )}

            {!meta.supports_embeddings && (
              <p className="text-xs text-muted-foreground">
                {meta.label} has no embeddings endpoint. Configure a different provider
                for document retrieval.
              </p>
            )}

            {testResult && (
              <div
                className={cn(
                  "flex items-start gap-2 rounded-md border px-3 py-2 text-xs",
                  testResult.ok
                    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                    : "border-destructive/30 bg-destructive/10 text-destructive",
                )}
              >
                {testResult.ok ? (
                  <CheckCircle2 className="size-3.5 shrink-0" />
                ) : (
                  <XCircle className="size-3.5 shrink-0" />
                )}
                <span>
                  {testResult.detail}
                  {testResult.models_available != null &&
                    ` (${testResult.models_available} models)`}
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-border px-4 py-3">
          <Button variant="outline" onClick={handleTest} disabled={testing}>
            {testing ? (
              <>
                <Loader2 className="size-3.5 animate-spin" /> Testing…
              </>
            ) : (
              "Test connection"
            )}
          </Button>
          <Button variant="accent" onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Save & set active"}
          </Button>
        </div>
      </div>
    </Backdrop>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs text-muted-foreground">{label}</label>
      {children}
    </div>
  );
}

function Backdrop({
  children,
  onClose,
}: {
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onMouseDown={onClose}
    >
      <div onMouseDown={(e) => e.stopPropagation()} className="w-full max-w-2xl">
        {children}
      </div>
    </div>
  );
}

function Loading() {
  return (
    <div className="flex items-center justify-center rounded-lg border border-border bg-popover p-10">
      <Loader2 className="size-5 animate-spin text-muted-foreground" />
    </div>
  );
}
