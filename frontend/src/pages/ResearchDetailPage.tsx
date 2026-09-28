import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { Download, FileJson, FileText as FileTextIcon, ExternalLink, ArrowLeft } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { api } from "@/lib/api";
import type {
  ResearchStatus, ReportData, SourceItem, CompetitorItem, TrendItem, RecommendationItem,
} from "@/types";
import { ProgressChecklist } from "@/components/ProgressChecklist";
import { EvidenceRing } from "@/components/EvidenceRing";
import { DemoBadge } from "@/components/DemoBadge";
import { SectionValue } from "@/components/SectionValue";

type Tab = "report" | "sources" | "competitors" | "trends";

const REPORT_SECTION_ORDER = [
  "executive_summary", "research_scope", "market_overview", "market_size_growth",
  "key_market_drivers", "market_challenges", "customer_segments", "competitive_landscape",
  "competitor_comparison", "market_trends", "recent_developments", "customer_sentiment",
  "swot_analysis", "opportunities", "threats", "strategic_recommendations",
  "key_takeaways", "confidence_assessment",
];

const DIRECTION_COLOR: Record<string, string> = {
  emerging: "#c97a3d",
  growing: "#3f9c82",
  stable: "#7c8797",
  declining: "#c1554b",
};

export function ResearchDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [status, setStatus] = useState<ResearchStatus | null>(null);
  const [report, setReport] = useState<ReportData | null>(null);
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [competitors, setCompetitors] = useState<CompetitorItem[]>([]);
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [tab, setTab] = useState<Tab>("report");

  const loadResults = useCallback(async (id: string) => {
    const [rep, src, comp, trd, recs] = await Promise.all([
      api.getReport(id),
      api.getSources(id),
      api.getCompetitors(id),
      api.getTrends(id),
      api.getRecommendations(id),
    ]);
    setReport(rep);
    setSources(src);
    setCompetitors(comp);
    setTrends(trd);
    setRecommendations(recs);
  }, []);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    const poll = async () => {
      try {
        const s = await api.getStatus(jobId);
        if (cancelled) return;
        setStatus(s);
        if (s.status === "completed") {
          await loadResults(jobId);
        } else if (s.status !== "failed") {
          timer = setTimeout(poll, 900);
        }
      } catch {
        if (!cancelled) timer = setTimeout(poll, 1500);
      }
    };
    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [jobId, loadResults]);

  const doExport = async (fmt: "json" | "markdown" | "pdf") => {
    if (!jobId) return;
    const blob = await api.exportReport(jobId, fmt);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `marketlens-report.${fmt === "markdown" ? "md" : fmt}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!status) {
    return <div className="p-8 text-sm text-muted">Loading…</div>;
  }

  const completedSteps = status.steps_log.map((s) => s.step);
  const isRunning = status.status !== "completed" && status.status !== "failed";

  if (isRunning) {
    return (
      <div className="mx-auto max-w-lg px-8 py-16 text-center">
        <h1 className="font-display text-2xl font-semibold text-paper">Running research…</h1>
        <p className="mt-1 text-sm text-muted">This usually takes a few seconds in demo mode.</p>
        <div className="mt-8 rounded-lg border border-line bg-surface p-6 text-left">
          <ProgressChecklist completedSteps={completedSteps} currentStep={status.current_step} />
        </div>
      </div>
    );
  }

  if (status.status === "failed") {
    return (
      <div className="mx-auto max-w-lg px-8 py-16 text-center">
        <h1 className="font-display text-2xl font-semibold text-alert">Research failed</h1>
        <p className="mt-2 text-sm text-muted">{status.error_message}</p>
        <Link to="/research" className="mt-6 inline-block text-sm text-verified hover:underline">
          Try a new research query
        </Link>
      </div>
    );
  }

  if (!report) {
    return <div className="p-8 text-sm text-muted">Loading report…</div>;
  }

  const riskColorKey = report.risk_level === "high" ? "declining" : report.risk_level === "medium" ? "emerging" : "growing";

  return (
    <div className="mx-auto max-w-4xl px-8 py-8">
      <Link to="/dashboard" className="mb-4 inline-flex items-center gap-1.5 text-xs text-muted hover:text-paper">
        <ArrowLeft size={14} /> Back to dashboard
      </Link>

      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-semibold text-paper">{report.title}</h1>
          <div className="mt-2 flex items-center gap-3">
            <EvidenceRing confidence={report.overall_confidence} sourceCount={sources.length} />
            <span className="font-mono text-xs uppercase tracking-wide text-muted">
              Risk: <span style={{ color: DIRECTION_COLOR[riskColorKey] }}>{report.risk_level}</span>
            </span>
            {sources.some((s) => s.is_demo) && <DemoBadge />}
          </div>
        </div>
        <div className="flex shrink-0 gap-2">
          <button
            onClick={() => doExport("pdf")}
            className="flex items-center gap-1.5 rounded-md border border-line px-3 py-1.5 text-xs text-paper hover:border-verified hover:text-verified"
          >
            <Download size={13} /> PDF
          </button>
          <button
            onClick={() => doExport("markdown")}
            className="flex items-center gap-1.5 rounded-md border border-line px-3 py-1.5 text-xs text-paper hover:border-verified hover:text-verified"
          >
            <FileTextIcon size={13} /> MD
          </button>
          <button
            onClick={() => doExport("json")}
            className="flex items-center gap-1.5 rounded-md border border-line px-3 py-1.5 text-xs text-paper hover:border-verified hover:text-verified"
          >
            <FileJson size={13} /> JSON
          </button>
        </div>
      </div>

      <div className="mb-6 flex gap-1 border-b border-line">
        {(["report", "sources", "competitors", "trends"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`border-b-2 px-3 py-2 text-sm capitalize transition-colors ${
              tab === t ? "border-verified text-paper" : "border-transparent text-muted hover:text-paper"
            }`}
          >
            {t} {t === "sources" && `(${sources.length})`}
            {t === "competitors" && `(${competitors.length})`}
            {t === "trends" && `(${trends.length})`}
          </button>
        ))}
      </div>

      {tab === "report" && (
        <div className="space-y-8">
          {REPORT_SECTION_ORDER.filter((k) => k in report.sections).map((key) => (
            <section key={key}>
              <h2 className="mb-2 font-display text-base font-semibold text-paper">
                {key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </h2>
              <SectionValue value={report.sections[key]} />
            </section>
          ))}

          {recommendations.length > 0 && (
            <section>
              <h2 className="mb-3 font-display text-base font-semibold text-paper">Prioritized Recommendations</h2>
              <div className="space-y-3">
                {recommendations.map((r) => (
                  <div key={r.id} className="rounded-lg border border-line bg-surface p-4">
                    <div className="mb-2 flex items-start justify-between gap-3">
                      <p className="text-sm font-medium text-paper">{r.recommendation}</p>
                      <EvidenceRing confidence={r.confidence} size={28} />
                    </div>
                    <p className="text-xs text-muted">{r.rationale}</p>
                    <div className="mt-2 flex gap-4 font-mono text-[11px] text-faint">
                      {r.expected_impact && <span>Impact: {r.expected_impact}</span>}
                      {r.risk && <span>Risk: {r.risk}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      {tab === "sources" && (
        <div className="space-y-2">
          {sources.map((s) => (
            <a
              key={s.id}
              href={s.url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-between gap-3 rounded-md border border-line bg-surface p-3 transition-colors hover:border-faint"
            >
              <div className="min-w-0">
                <div className="truncate text-sm text-paper">{s.title}</div>
                <div className="mt-0.5 font-mono text-[11px] text-muted">
                  {s.publisher} · {s.source_type}
                  {s.published_at && ` · ${new Date(s.published_at).toLocaleDateString()}`}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <EvidenceRing confidence={s.relevance_score} size={26} />
                <ExternalLink size={14} className="text-faint" />
              </div>
            </a>
          ))}
        </div>
      )}

      {tab === "competitors" && (
        <div className="space-y-4">
          {competitors.length > 0 && (
            <div className="h-48 rounded-lg border border-line bg-surface p-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={competitors.map((c) => ({ name: c.company_name, score: c.market_position_score ?? 0 }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#262e38" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: "#7c8797", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#7c8797", fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ background: "#151b23", border: "1px solid #262e38", fontSize: 12 }}
                  />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                    {competitors.map((_, i) => (
                      <Cell key={i} fill="#3f9c82" />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          {competitors.map((c) => (
            <div key={c.id} className="rounded-lg border border-line bg-surface p-4">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="font-display text-base font-semibold text-paper">{c.company_name}</h3>
                {c.market_position_score !== null && (
                  <span className="font-mono text-xs text-muted">Position: {c.market_position_score}</span>
                )}
              </div>
              <p className="text-sm text-paper/90">{c.positioning}</p>
              <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                <div>
                  <div className="mb-1 font-mono uppercase tracking-wide text-verified">Strengths</div>
                  <ul className="list-inside list-disc text-paper/80">
                    {c.strengths.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </div>
                <div>
                  <div className="mb-1 font-mono uppercase tracking-wide text-alert">Weaknesses</div>
                  <ul className="list-inside list-disc text-paper/80">
                    {c.weaknesses.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "trends" && (
        <div className="space-y-3">
          {trends.map((t) => (
            <div key={t.id} className="rounded-lg border border-line bg-surface p-4">
              <div className="mb-1.5 flex items-start justify-between gap-3">
                <h3 className="text-sm font-medium text-paper">{t.name}</h3>
                <span
                  className="shrink-0 font-mono text-[11px] uppercase tracking-wide"
                  style={{ color: DIRECTION_COLOR[t.direction] }}
                >
                  {t.direction}
                </span>
              </div>
              <p className="text-sm text-paper/80">{t.description}</p>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-xs text-muted">{t.business_impact}</span>
                <EvidenceRing confidence={t.confidence} sourceCount={t.source_count} size={28} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
