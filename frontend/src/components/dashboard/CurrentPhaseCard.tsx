
import { BrutalCard } from "../brutal/BrutalCard";

export function CurrentPhaseCard() {
  return (
    <div className="current-phase-card__container">
      <BrutalCard className="current-phase-card" accent="blue">
        <h2 className="current-phase-card__title">CURRENT PHASE</h2>
        <p className="current-phase-card__description">
          Your current phase in the learning journey.
        </p>
      </BrutalCard>
    </div>
  );
}
