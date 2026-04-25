
import { BrutalCard } from "../brutal/BrutalCard";

export function MetricsCard() {
  return (
    <div className="metrics-card__container">
      <BrutalCard className="metrics-card" accent="blue">
        <h2 className="metrics-card__title">METRICS</h2>
        <p className="metrics-card__description">
          Your performance in the last session.
        </p>
      </BrutalCard>
    </div>
  );
}
