import type { ReactNode } from "react";

interface BrutalCardProps {
  children: ReactNode;
  accent?: "yellow" | "green" | "red" | "blue" | "white" | "muted";
  className?: string;
  testId?: string;
}

export function BrutalCard({ children, accent = "white", className, testId }: BrutalCardProps) {
  const accentClass = `brutal-card--${accent}`;
  return (
    <section data-testid={testId} className={`brutal-card ${accentClass} ${className ?? ""}`.trim()}>
      {children}
    </section>
  );
}
