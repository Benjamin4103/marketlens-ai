import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileStack, Users, TrendingUp, FileText, LogOut } from "lucide-react";
import { api } from "@/lib/api";
import type { ResearchProject } from "@/types";
import { useAuth } from "@/stores/auth";

function ProjectListShell({
  icon: Icon,
  title,
  blurb,
}: {
  icon: any;
  title: string;
  blurb: string;
}) {
  const [projects, setProjects] = useState<ResearchProject[]>([]);

  useEffect(() => {
    api.listResearch().then(setProjects);
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-8 py-10">
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-verified-dim text-verified">
          <Icon size={18} />
        </div>
        <div>
          <h1 className="font-display text-xl font-semibold text-paper">{title}</h1>
          <p className="text-sm text-muted">{blurb}</p>
        </div>
      </div>

      {projects.length === 0 ? (
        <p className="text-sm text-muted">
          No research yet. <Link to="/research" className="text-verified hover:underline">Start one</Link>.
        </p>
      ) : (
        <div className="space-y-2">
          {projects.map((p) => (
            <Link
              key={p.id}
              to={`/research-project/${p.id}`}
              className="flex items-center justify-between rounded-md border border-line bg-surface p-3 hover:border-faint"
            >
              <span className="text-sm text-paper">{p.title}</span>
              <span className="text-xs text-verified">View →</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export function SourcesPage() {
  return (
    <ProjectListShell
      icon={FileStack}
      title="Sources"
      blurb="Every source is attached to a research run — select one to browse its citations."
    />
  );
}

export function CompetitorsPage() {
  return (
    <ProjectListShell
      icon={Users}
      title="Competitors"
      blurb="Competitor comparisons are grouped per research run."
    />
  );
}

export function TrendsPage() {
  return (
    <ProjectListShell
      icon={TrendingUp}
      title="Trends"
      blurb="Market trends are grouped per research run."
    />
  );
}

export function ReportsPage() {
  return (
    <ProjectListShell
      icon={FileText}
      title="Reports"
      blurb="All generated market intelligence reports."
    />
  );
}

export function SettingsPage() {
  const { user, logout } = useAuth();
  return (
    <div className="mx-auto max-w-2xl px-8 py-10">
      <h1 className="mb-6 font-display text-xl font-semibold text-paper">Settings</h1>
      <div className="rounded-lg border border-line bg-surface p-5">
        <div className="mb-4">
          <div className="font-mono text-xs uppercase tracking-wide text-muted">Signed in as</div>
          <div className="text-sm text-paper">{user?.email}</div>
        </div>
        <div className="mb-4">
          <div className="font-mono text-xs uppercase tracking-wide text-muted">Mode</div>
          <div className="text-sm text-paper">
            Demo mode — reports use clearly labeled simulated data. Configure API keys on the
            backend (.env) to enable live research.
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-1.5 rounded-md border border-line px-3 py-1.5 text-xs text-alert hover:border-alert"
        >
          <LogOut size={13} /> Sign out
        </button>
      </div>
    </div>
  );
}
