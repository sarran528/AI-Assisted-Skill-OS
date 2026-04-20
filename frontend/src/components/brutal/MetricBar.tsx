interface MetricBarProps {
  label: string;
  value: number;
  max?: number;
}

export function MetricBar({ label, value, max = 1 }: MetricBarProps) {
  const clamped = Math.max(0, Math.min(max, value));
  const percent = (clamped / max) * 100;

  return (
    <div className="metric-row">
      <span className="metric-row__label">{label}</span>
      <div className="metric-row__bar">
        <div className="metric-row__fill" style={{ width: `${percent}%` }} />
      </div>
      <span className="metric-row__value">{clamped.toFixed(2)}</span>
    </div>
  );
}
