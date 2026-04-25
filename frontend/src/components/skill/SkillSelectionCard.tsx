
import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export function SkillSelectionCard() {
  return (
    <div className="skill-selection-card__container">
      <BrutalCard className="skill-selection-card" accent="blue">
        <h2 className="skill-selection-card__title">SELECT SKILL</h2>
        <p className="skill-selection-card__description">
          Choose a skill to begin your journey.
        </p>
        <BrutalButton
          data-testid="skill-selection-action"
          variant="mono"
          className="skill-selection-card__button"
        >
          Select Skill
        </BrutalButton>
      </BrutalCard>
    </div>
  );
}
