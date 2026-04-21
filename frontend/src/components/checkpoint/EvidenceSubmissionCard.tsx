
import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export function EvidenceSubmissionCard() {
  return (
    <div className="evidence-submission-card__container">
      <BrutalCard className="evidence-submission-card" accent="blue">
        <h2 className="evidence-submission-card__title">EVIDENCE SUBMISSION</h2>
        <p className="evidence-submission-card__description">
          Upload your work for validation.
        </p>
        <BrutalButton
          data-testid="evidence-submission-action"
          variant="mono"
          className="evidence-submission-card__button"
        >
          Submit Evidence
        </BrutalButton>
      </BrutalCard>
    </div>
  );
}
