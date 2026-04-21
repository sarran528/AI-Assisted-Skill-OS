import { AlertTriangle, BadgeCheck, Lightbulb } from "lucide-react";

import { BrutalCard } from "./BrutalCard";

interface TipCardProps {
  text: string;
  severity?: "minor" | "moderate" | "critical";
  focusStep?: string;
  testId?: string;
}

export function TipCard({ text, severity = "minor", focusStep, testId }: TipCardProps) {
  const accent = severity === "critical" ? "red" : severity === "moderate" ? "yellow" : "blue";
  const Icon = severity === "critical" ? AlertTriangle : severity === "moderate" ? Lightbulb : BadgeCheck;

  return (
    <BrutalCard accent={accent} className="tip-card" testId={testId}>
      <div className="tip-card__header">
        <Icon size={18} />
        <span>{severity.toUpperCase()} CORRECTION TIP</span>
      </div>
      <p>{text}</p>
      {focusStep ? <p className="tip-card__focus">Focus Step: {focusStep}</p> : null}
    </BrutalCard>
  );
}
