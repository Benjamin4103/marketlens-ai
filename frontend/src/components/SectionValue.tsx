const INSUFFICIENT = "Insufficient reliable data found.";

function EmptyNote() {
  return <p className="text-sm italic text-faint">{INSUFFICIENT}</p>;
}

export function SectionValue({ value }: { value: any }) {
  if (value === INSUFFICIENT || value == null) return <EmptyNote />;

  if (typeof value === "string") {
    return <p className="text-sm leading-relaxed text-paper/90">{value}</p>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return <EmptyNote />;
    if (typeof value[0] === "object") {
      return (
        <div className="space-y-3">
          {value.map((item, i) => (
            <div key={i} className="rounded-md border border-line bg-surface-raised p-3">
              {Object.entries(item).map(([k, v]) => (
                <div key={k} className="mb-1 last:mb-0 text-sm">
                  <span className="font-mono text-xs uppercase tracking-wide text-muted">
                    {k.replace(/_/g, " ")}:{" "}
                  </span>
                  <span className="text-paper/90">
                    {Array.isArray(v) ? (v as any[]).join(", ") : String(v)}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      );
    }
    return (
      <ul className="list-inside list-disc space-y-1 text-sm text-paper/90">
        {value.map((v, i) => (
          <li key={i}>{String(v)}</li>
        ))}
      </ul>
    );
  }

  if (typeof value === "object") {
    return (
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        {Object.entries(value).map(([k, v]) => (
          <div key={k}>
            <dt className="font-mono text-xs uppercase tracking-wide text-muted">{k.replace(/_/g, " ")}</dt>
            <dd className="text-paper/90">{Array.isArray(v) ? (v as any[]).join(", ") : String(v)}</dd>
          </div>
        ))}
      </dl>
    );
  }

  return <p className="text-sm text-paper/90">{String(value)}</p>;
}
