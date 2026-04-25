
import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export function JournalEntryCard() {
  return (
    <div className="journal-entry-card__container">
      <BrutalCard className="journal-entry-card" accent="blue">
        <h2 className="journal-entry-card__title">JOURNAL ENTRY</h2>
        <p className="journal-entry-card__description">
          What's on your mind?
        </p>
        <BrutalButton
          data-testid="journal-entry-action"
          variant="mono"
          className="journal-entry-card__button"
        >
          Save Entry
        </BrutalButton>
      </BrutalCard>
    </div>
  );
}
