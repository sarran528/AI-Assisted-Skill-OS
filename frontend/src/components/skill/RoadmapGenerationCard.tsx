
import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export function RoadmapGenerationCard() {
  return (
    <div className="roadmap-generation-card__container">
      <BrutalCard className="roadmap-generation-card" accent="blue">
        <h2 className="roadmap-generation-card__title">ROADMAP GENERATION</h2>
        <p className="roadmap-generation-card__description">
          Generating your personalized learning roadmap.
        </p>
        <BrutalButton
          data-testid="roadmap-generation-action"
          variant="mono"
          className="roadmap-generation-card__button"
        >
          View Roadmap
        </BrutalButton>
      </BrutalCard>
    </div>
  );
}
