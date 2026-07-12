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
