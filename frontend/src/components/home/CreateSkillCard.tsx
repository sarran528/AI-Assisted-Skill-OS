import { useNavigate } from "react-router-dom";
import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";
import { Input } from "../ui/Input";

/**
 * CreateSkillCard
 * 
 * Displayed in pre-skill state (no skills created).
 * Single-purpose entry point to skill creation flow.
 * 
 * Conditions:
 * - SkillRoadmap == null
 * - BaselineSkillState == null
 */
export function CreateSkillCard() {
  const navigate = useNavigate();

  return (
    <div className="create-skill-card__container">
      <BrutalCard className="create-skill-card" accent="blue">
        <h2 className="create-skill-card__title">CREATE SKILL</h2>
        <p className="create-skill-card__description">
          Select domain → complete grounding → generate roadmap
        </p>
        <Input placeholder="Enter a skill..." />
        <BrutalButton
          data-testid="create-skill-action"
          variant="mono"
          onClick={() => navigate("/skills/new")}
          className="create-skill-card__button"
        >
          Create Skill
        </BrutalButton>
      </BrutalCard>
    </div>
  );
}
