export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center px-6">
      <div className="space-y-6">
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-accent" />
          Phase 0 · Foundation
        </div>

        <div className="space-y-3">
          <h1 className="text-3xl font-semibold tracking-tight">InterviewOS</h1>
          <p className="text-balance text-muted-foreground">
            An AI-powered interview preparation workspace. It combines your notes,
            books, slides, and resume with live knowledge — routed by a planner agent
            that decides what to retrieve before it answers.
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-4 text-sm text-muted-foreground">
          The scaffold is up. The workspace shell, document pipeline, and planner-first
          RAG chat arrive in the phases ahead.
        </div>
      </div>
    </main>
  );
}
