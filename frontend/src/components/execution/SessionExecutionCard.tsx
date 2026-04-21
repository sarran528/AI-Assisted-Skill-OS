
import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export function SessionExecutionCard() {
  return (
    <div className="session-execution-card__container">
      <BrutalCard className="session-execution-card" accent="blue">
        <h2 className="session-execution-card__title">SESSION EXECUTION</h2>
        <p className="session-execution-card__description">
          Complete the task as instructed.
        </p>
        <BrutalButton
          data-testid="session-execution-action"
          variant="mono"
          className="session-execution-card__button"
        >
          Submit Session
        </BrutalButton>
      </BrutalCard>
    </div>
  );
}
