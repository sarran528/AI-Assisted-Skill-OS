interface StatBlockProps {
  value: string;
  label: string;
  accent?: boolean;
}

export function StatBlock({ value, label, accent = false }: StatBlockProps) {
  return (
    <article className={`stat-block ${accent ? "stat-block--accent" : ""}`.trim()}>
      <div className="stat-block__value">{value}</div>
      <div className="stat-block__label">{label}</div>
    </article>
  );
}
