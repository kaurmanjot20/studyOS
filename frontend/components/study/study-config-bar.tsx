"use client";

import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/** Shared top bar for study generators: a subject input, optional extra controls,
 * and a Generate button. */
export function StudyConfigBar({
  subject,
  onSubject,
  onGenerate,
  loading,
  cta,
  extra,
}: {
  subject: string;
  onSubject: (v: string) => void;
  onGenerate: () => void;
  loading: boolean;
  cta: string;
  extra?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Input
        value={subject}
        onChange={(e) => onSubject(e.target.value)}
        placeholder="Topic (e.g. Deadlocks, TCP, SQL joins)…"
        className="min-w-[180px] flex-1"
        onKeyDown={(e) => e.key === "Enter" && !loading && onGenerate()}
      />
      {extra}
      <Button variant="accent" onClick={onGenerate} disabled={loading}>
        {loading ? <Loader2 className="size-4 animate-spin" /> : cta}
      </Button>
    </div>
  );
}
