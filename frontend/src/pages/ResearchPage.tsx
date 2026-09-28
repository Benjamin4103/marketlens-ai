import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, X, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import type { ResearchDepth } from "@/types";

const DEPTHS: { value: ResearchDepth; label: string; blurb: string }[] = [
  { value: "quick", label: "Quick", blurb: "Fast overview, fewer sources" },
  { value: "standard", label: "Standard", blurb: "Balanced depth and speed" },
  { value: "deep", label: "Deep", blurb: "Most thorough, more sources" },
];

export function ResearchPage() {
  const [query, setQuery] = useState("");
  const [geography, setGeography] = useState("");
  const [timePeriod, setTimePeriod] = useState("");
  const [depth, setDepth] = useState<ResearchDepth>("standard");
  const [competitors, setCompetitors] = useState<string[]>([]);
  const [competitorInput, setCompetitorInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const addCompetitor = () => {
    const v = competitorInput.trim();
    if (v && !competitors.includes(v)) {
      setCompetitors([...competitors, v]);
      setCompetitorInput("");
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const job = await api.createResearch({
        query: query.trim(),
        geography: geography.trim() || undefined,
        time_period: timePeriod.trim() || undefined,
        depth,
        competitors,
      });
      await api.runResearch(job.id);
      navigate(`/research/${job.id}`);
    } catch (err: any) {
      setError(err.message || "Could not start research");
      setLoading(false);
    }
  };

  const EXAMPLES = ["Indian electric vehicle market", "Zomato vs Swiggy", "Global SaaS market", "Tesla"];

  return (
    <div className="mx-auto max-w-2xl px-8 py-12">
      <h1 className="font-display text-3xl font-semibold text-paper">What market do you want to research?</h1>
      <p className="mt-2 text-sm text-muted">
        Enter a market, company, or comparison. MarketLens will run a structured, source-backed research
        pipeline and hand you an evidence-graded report.
      </p>

      <form onSubmit={submit} className="mt-8 space-y-5">
        <div>
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Indian electric vehicle market"
            className="w-full rounded-lg border border-line bg-surface px-4 py-3 text-base text-paper placeholder:text-faint focus:border-verified focus:outline-none"
          />
          <div className="mt-2 flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                type="button"
                key={ex}
                onClick={() => setQuery(ex)}
                className="rounded-full border border-line px-2.5 py-1 text-xs text-muted transition-colors hover:border-verified hover:text-verified"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1.5 block text-xs font-mono uppercase tracking-wide text-muted">
              Geography
            </label>
            <input
              value={geography}
              onChange={(e) => setGeography(e.target.value)}
              placeholder="Optional"
              className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-paper placeholder:text-faint focus:border-verified focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-mono uppercase tracking-wide text-muted">
              Time period
            </label>
            <input
              value={timePeriod}
              onChange={(e) => setTimePeriod(e.target.value)}
              placeholder="Optional"
              className="w-full rounded-md border border-line bg-surface px-3 py-2 text-sm text-paper placeholder:text-faint focus:border-verified focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-mono uppercase tracking-wide text-muted">
            Research depth
          </label>
          <div className="grid grid-cols-3 gap-2">
            {DEPTHS.map((d) => (
              <button
                type="button"
                key={d.value}
                onClick={() => setDepth(d.value)}
                className={`rounded-md border px-3 py-2 text-left transition-colors ${
                  depth === d.value
                    ? "border-verified bg-verified-dim"
                    : "border-line bg-surface hover:border-faint"
                }`}
              >
                <div className={`text-sm font-medium ${depth === d.value ? "text-verified" : "text-paper"}`}>
                  {d.label}
                </div>
                <div className="text-[11px] text-muted">{d.blurb}</div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-mono uppercase tracking-wide text-muted">
            Competitors to include (optional)
          </label>
          <div className="flex gap-2">
            <input
              value={competitorInput}
              onChange={(e) => setCompetitorInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addCompetitor();
                }
              }}
              placeholder="Add a competitor name"
              className="flex-1 rounded-md border border-line bg-surface px-3 py-2 text-sm text-paper placeholder:text-faint focus:border-verified focus:outline-none"
            />
            <button
              type="button"
              onClick={addCompetitor}
              className="flex items-center justify-center rounded-md border border-line px-3 text-muted hover:border-verified hover:text-verified"
            >
              <Plus size={16} />
            </button>
          </div>
          {competitors.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {competitors.map((c) => (
                <span
                  key={c}
                  className="flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1 text-xs text-paper"
                >
                  {c}
                  <button
                    type="button"
                    onClick={() => setCompetitors(competitors.filter((x) => x !== c))}
                    className="text-muted hover:text-alert"
                  >
                    <X size={12} />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {error && <p className="text-sm text-alert">{error}</p>}

        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-verified py-3 text-sm font-medium text-ink transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Starting research…" : "Start Research"}
          {!loading && <ArrowRight size={16} />}
        </button>
      </form>
    </div>
  );
}
