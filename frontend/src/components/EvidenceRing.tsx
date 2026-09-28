interface EvidenceRingProps {
  confidence: number; // 0-1
  sourceCount?: number;
  size?: number;
  label?: string;
}

/**
 * The signature visual motif of MarketLens AI: every claim in the app
 * (trend, insight, recommendation, metric) is paired with an Evidence Ring —
 * a small stroke-based ring showing confidence, plus how many sources back
 * it. This makes the "traceable claim" principle from the spec a literal,
 * repeated visual element rather than a one-off badge.
 */
export function EvidenceRing({ confidence, sourceCount, size = 34, label }: EvidenceRingProps) {
  const pct = Math.round(confidence * 100);
  const radius = (size - 4) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - confidence);

  const tone =
    confidence >= 0.7 ? "var(--color-verified)" : confidence >= 0.45 ? "var(--color-signal)" : "var(--color-alert)";

  return (
    <div className="inline-flex items-center gap-2" title={label ?? `${pct}% confidence`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="shrink-0">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-line)"
          strokeWidth={3}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={tone}
          strokeWidth={3}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
        <text
          x="50%"
          y="50%"
          dominantBaseline="middle"
          textAnchor="middle"
          fontFamily="var(--font-mono)"
          fontSize={size * 0.28}
          fill="var(--color-paper)"
        >
          {pct}
        </text>
      </svg>
      {sourceCount !== undefined && (
        <span className="font-mono text-xs text-muted">
          {sourceCount} {sourceCount === 1 ? "source" : "sources"}
        </span>
      )}
    </div>
  );
}
