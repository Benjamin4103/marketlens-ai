import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Clock, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import type { ResearchProject } from "@/types";

export function DashboardPage() {
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listResearch()
      .then(setProjects)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-8 py-10">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold text-paper">Dashboard</h1>
          <p className="mt-1 text-sm text-muted">Your research history and saved reports.</p>
        </div>
        <Link
          to="/research"
          className="flex items-center gap-1.5 rounded-md bg-verified px-4 py-2 text-sm font-medium text-ink hover:opacity-90"
        >
          <Plus size={16} /> New Research
        </Link>
      </div>

      {loading && <p className="text-sm text-muted">Loading…</p>}

      {!loading && projects.length === 0 && (
        <div className="rounded-xl border border-dashed border-line p-10 text-center">
          <p className="text-sm text-muted">No research yet. Start your first market intelligence report.</p>
          <Link
            to="/research"
            className="mt-4 inline-flex items-center gap-1.5 text-sm text-verified hover:underline"
          >
            Start research <ArrowRight size={14} />
          </Link>
        </div>
      )}

      <div className="space-y-2">
        {projects.map((p) => (
          <div
            key={p.id}
            className="flex items-center justify-between rounded-lg border border-line bg-surface p-4"
          >
            <div>
              <div className="font-display text-base font-medium text-paper">{p.title}</div>
              <div className="mt-1 flex items-center gap-1.5 font-mono text-[11px] text-muted">
                <Clock size={11} />
                {new Date(p.created_at).toLocaleString()}
                <span className="rounded-full border border-line px-1.5 py-0.5 uppercase">{p.subject_type}</span>
              </div>
            </div>
            <Link to={`/research-project/${p.id}`} className="text-sm text-verified hover:underline">
              View →
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
