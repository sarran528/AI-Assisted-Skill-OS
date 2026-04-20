import { Lock, CheckCircle2 } from "lucide-react";

import { BrutalButton } from "./BrutalButton";
import { BrutalCard } from "./BrutalCard";

interface PhaseCardProps {
  phase: string;
  status: "locked" | "active" | "completed";
  estimatedWeeks: number;
  onEnter?: () => void;
  testId?: string;
}

export function PhaseCard({ phase, status, estimatedWeeks, onEnter, testId }: PhaseCardProps) {
  const accent = status === "active" ? "yellow" : status === "completed" ? "green" : "muted";

  return (
    <BrutalCard accent={accent} className="phase-card" testId={testId}>
      <div className="phase-card__title">{phase}</div>
      <div className="phase-card__meta">{estimatedWeeks} weeks</div>
      <div className="phase-card__status">{status.toUpperCase()}</div>
      {status === "locked" && <Lock size={16} />}
      {status === "completed" && <CheckCircle2 size={16} />}
      {status === "active" && (
        <BrutalButton variant="primary" onClick={onEnter} data-testid="enter-phase-btn">
          Enter Phase
        </BrutalButton>
      )}
    </BrutalCard>
  );
}
