import { Check, Loader2, Circle } from "lucide-react";

const ALL_STEPS = [
  "Research plan created",
  "Searching sources",
  "Collecting news",
  "Identifying competitors",
  "Cleaning & chunking documents",
  "Analyzing trends",
  "Generating strategic insights",
  "Final verification",
];

export function ProgressChecklist({
  completedSteps,
  currentStep,
}: {
  completedSteps: string[];
  currentStep: string | null;
}) {
  return (
    <div className="space-y-2.5">
      {ALL_STEPS.map((step) => {
        const done = completedSteps.includes(step);
        const active = !done && step === currentStep;
        return (
          <div key={step} className="flex items-center gap-3 font-mono text-sm">
            {done ? (
              <Check size={16} className="text-verified" />
            ) : active ? (
              <Loader2 size={16} className="animate-spin text-signal" />
            ) : (
              <Circle size={14} className="text-faint" />
            )}
            <span className={done ? "text-paper" : active ? "text-signal" : "text-muted"}>{step}</span>
          </div>
        );
      })}
    </div>
  );
}
