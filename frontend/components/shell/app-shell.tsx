"use client";

import * as React from "react";

import { type Trace } from "@/components/chat/chat-view";
import { Center, type WorkspaceMode } from "@/components/shell/center";
import { LeftSidebar } from "@/components/shell/left-sidebar";
import { RightSidebar } from "@/components/shell/right-sidebar";
import { TopNav } from "@/components/shell/top-nav";
import { SettingsDialog } from "@/components/settings/settings-dialog";
import { CreateWorkspaceDialog } from "@/components/workspace/create-workspace-dialog";
import { api, ApiError } from "@/lib/api";
import type { Workspace, WorkspaceCreate } from "@/lib/types";

/** The three-pane application shell. Owns workspace list + selection state. */
export function AppShell() {
  const [workspaces, setWorkspaces] = React.useState<Workspace[]>([]);
  const [activeId, setActiveId] = React.useState<string | null>(null);
  const [mode, setMode] = React.useState<WorkspaceMode>("chat");
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [settingsOpen, setSettingsOpen] = React.useState(false);
  const [activeProviderLabel, setActiveProviderLabel] = React.useState<
    string | null
  >(null);
  const [trace, setTrace] = React.useState<Trace>({ plan: null, sources: [] });

  const loadActiveProvider = React.useCallback(async () => {
    try {
      const [settings, providers] = await Promise.all([
        api.settings.list(),
        api.settings.providers(),
      ]);
      const active = settings.find((s) => s.is_active);
      const label = providers.find((p) => p.name === active?.provider)?.label;
      setActiveProviderLabel(label ?? null);
    } catch {
      setActiveProviderLabel(null);
    }
  }, []);

  const loadWorkspaces = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await api.workspaces.list();
      setWorkspaces(list);
      setActiveId((current) => current ?? list[0]?.id ?? null);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? `Could not reach the backend (${err.status}).`
          : "Could not reach the backend. Is it running?",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadWorkspaces();
    loadActiveProvider();
  }, [loadWorkspaces, loadActiveProvider]);

  const handleCreate = async (data: WorkspaceCreate) => {
    setSubmitting(true);
    try {
      const created = await api.workspaces.create(data);
      setWorkspaces((prev) => [created, ...prev]);
      setActiveId(created.id);
      setDialogOpen(false);
    } catch {
      setError("Failed to create the workspace.");
    } finally {
      setSubmitting(false);
    }
  };

  const activeWorkspace =
    workspaces.find((w) => w.id === activeId) ?? null;

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <TopNav
        activeWorkspace={activeWorkspace}
        activeProviderLabel={activeProviderLabel}
        onOpenWorkspaces={() => setDialogOpen(true)}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      {error && (
        <div className="flex items-center justify-between border-b border-destructive/40 bg-destructive/10 px-3 py-1.5 text-xs text-destructive">
          <span>{error}</span>
          <button className="underline" onClick={loadWorkspaces}>
            Retry
          </button>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        <LeftSidebar
          workspaces={workspaces}
          activeWorkspaceId={activeId}
          loading={loading}
          onSelect={setActiveId}
          onCreate={() => setDialogOpen(true)}
        />
        <Center
          workspace={activeWorkspace}
          mode={mode}
          onModeChange={setMode}
          onTrace={setTrace}
        />
        <RightSidebar trace={trace} />
      </div>

      <CreateWorkspaceDialog
        open={dialogOpen}
        submitting={submitting}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleCreate}
      />

      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSaved={loadActiveProvider}
      />
    </div>
  );
}
