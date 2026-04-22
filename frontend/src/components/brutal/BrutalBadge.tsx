import type { ReactNode } from "react";

interface BrutalBadgeProps {
  children: ReactNode;
  accent?: "yellow" | "green" | "red" | "blue" | "white" | "muted";
  className?: string;
}

export function BrutalBadge({ children, accent = "white", className }: BrutalBadgeProps) {
  const accentClass = `brutal-card--${accent}`;
  return (
    <span className={`inline-flex items-center rounded-sm border-2 border-black px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${accentClass} ${className ?? ""}`.trim()}>
      {children}
    </span>
  );
}
