
import { BrutalCard } from "../brutal/BrutalCard";

export function CheckpointCard() {
  return (
    <div className="checkpoint-card__container">
      <BrutalCard className="checkpoint-card" accent="blue">
        <h2 className="checkpoint-card__title">CHECKPOINT</h2>
        <p className="checkpoint-card__description">
          Review your progress and submit evidence.
        </p>
      </BrutalCard>
    </div>
  );
}
