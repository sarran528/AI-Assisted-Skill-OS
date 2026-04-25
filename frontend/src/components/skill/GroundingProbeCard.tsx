
import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export function GroundingProbeCard() {
  return (
    <div className="grounding-probe-card__container">
      <BrutalCard className="grounding-probe-card" accent="blue">
        <h2 className="grounding-probe-card__title">GROUNDING PROBE</h2>
        <p className="grounding-probe-card__description">
          Answer a few questions to personalize your roadmap.
        </p>
        <BrutalButton
          data-testid="grounding-probe-action"
          variant="mono"
          className="grounding-probe-card__button"
        >
          Submit Answers
        </BrutalButton>
      </BrutalCard>
    </div>
  );
}
