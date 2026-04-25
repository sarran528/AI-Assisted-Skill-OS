
import { BrutalCard } from "../brutal/BrutalCard";

export function JournalCard() {
  return (
    <div className="journal-card__container">
      <BrutalCard className="journal-card" accent="blue">
        <h2 className="journal-card__title">JOURNAL</h2>
        <p className="journal-card__description">
          Reflect on your journey.
        </p>
      </BrutalCard>
    </div>
  );
}
