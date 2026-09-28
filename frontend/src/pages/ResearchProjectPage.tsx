import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, RefreshCw, ArrowRight, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { ResearchProjectDetail, WhatChanged } from "@/types";

export function ResearchProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ResearchProjectDetail | null>(null);
  const [changed, setChanged] = useState<WhatChanged | null>(null);
  const [rerunning, setRerunning] = useState(false);

  const load = async () => {
    if (!projectId) return;
    const p = await api.getResearchProject(projectId);
    setProject(p);
    const c = await api.whatChanged(projectId);
    setChanged(c);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const rerun = async () => {
    if (!project || project.queries.length === 0) return;
    setRerunning(true);
    const lastQuery = project.queries[project.queries.length - 1];
    const job = await api.createResearch({
      query: lastQuery.raw_query,
      geography: lastQuery.geography ?? undefined,
      time_period: lastQuery.time_period ?? undefined,
      depth: lastQuery.depth,
      competitors: lastQuery.competitors_requested,
    });
    await api.runResearch(job.id);
    window.location.href = `/research/${job.id}`;
  };

  if (!project) return <div className="p-8 text-sm text-muted">Loading…</div>;

  const sortedJobs = [...project.jobs].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div className="mx-auto max-w-3xl px-8 py-10">
      <Link to="/dashboard" className="mb-4 inline-flex items-center gap-1.5 text-xs text-muted hover:text-paper">
        <ArrowLeft size={14} /> Back to dashboard
      </Link>

      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold text-paper">{project.title}</h1>
        <button
          onClick={rerun}
          disabled={rerunning}
          className="flex items-center gap-1.5 rounded-md border border-line px-3 py-1.5 text-xs text-paper hover:border-verified hover:text-verified disabled:opacity-50"
        >
          <RefreshCw size={13} className={rerunning ? "animate-spin" : ""} />
          Research again
        </button>
      </div>

      {changed && !changed.note && (
        <div className="mb-6 rounded-lg border border-signal/30 bg-signal-dim p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-signal">
            <Sparkles size={15} /> What Changed
          </div>
          <ul className="space-y-1 text-sm text-paper/90">
            {changed.new_competitors.map((c) => (
              <li key={c}>New competitor: {c}</li>
            ))}
            {changed.new_trends.map((t) => (
              <li key={t}>New trend: {t}</li>
            ))}
            {changed.changed_metrics.map((m) => (
              <li key={m.metric}>
                {m.metric.replace(/_/g, " ")}: {m.previous} → {m.current}
              </li>
            ))}
            {changed.new_risks.map((r) => (
              <li key={r}>{r}</li>
            ))}
            {changed.new_developments.length === 0 &&
              changed.new_competitors.length === 0 &&
              changed.new_trends.length === 0 &&
              changed.changed_metrics.length === 0 && (
                <li className="text-muted">No material changes detected since the last run.</li>
              )}
          </ul>
        </div>
      )}
      {changed?.note && <p className="mb-6 text-sm text-muted">{changed.note}</p>}

      <h2 className="mb-3 font-mono text-xs uppercase tracking-wide text-muted">Research runs</h2>
      <div className="space-y-2">
        {sortedJobs.map((j) => (
          <Link
            key={j.id}
            to={`/research/${j.id}`}
            className="flex items-center justify-between rounded-md border border-line bg-surface p-3 hover:border-faint"
          >
            <div>
              <div className="text-sm text-paper">{new Date(j.created_at).toLocaleString()}</div>
              <div className="font-mono text-[11px] text-muted">
                {j.status} · {j.sources_retrieved_count} sources
                {j.is_demo_mode ? " · demo" : ""}
              </div>
            </div>
            <ArrowRight size={14} className="text-faint" />
          </Link>
        ))}
      </div>
    </div>
  );
}
