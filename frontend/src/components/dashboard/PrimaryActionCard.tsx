
import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export function PrimaryActionCard() {
  return (
    <div className="primary-action-card__container">
      <BrutalCard className="primary-action-card" accent="blue">
        <h2 className="primary-action-card__title">PRIMARY ACTION</h2>
        <p className="primary-action-card__description">
          Your next step.
        </p>
        <BrutalButton
          data-testid="primary-action-action"
          variant="mono"
          className="primary-action-card__button"
        >
          Start
        </BrutalButton>
      </BrutalCard>
    </div>
  );
}
