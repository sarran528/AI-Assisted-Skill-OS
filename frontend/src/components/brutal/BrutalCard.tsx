import type { HTMLAttributes, ReactNode } from "react";

interface BrutalCardProps extends HTMLAttributes<HTMLElement> {
  children: ReactNode;
  accent?: "yellow" | "green" | "red" | "blue" | "white" | "muted";
  testId?: string;
}

export function BrutalCard({ children, accent = "white", className, testId, ...rest }: BrutalCardProps) {
  const accentClass = `brutal-card--${accent}`;
  return (
    <section data-testid={testId} className={`brutal-card ${accentClass} ${className ?? ""}`.trim()} {...rest}>
      {children}
    </section>
  );
}
