
import { BrutalCard } from "../brutal/BrutalCard";

export function RoadmapSnapshotCard() {
  return (
    <div className="roadmap-snapshot-card__container">
      <BrutalCard className="roadmap-snapshot-card" accent="blue">
        <h2 className="roadmap-snapshot-card__title">ROADMAP SNAPSHOT</h2>
        <p className="roadmap-snapshot-card__description">
          Your learning roadmap.
        </p>
      </BrutalCard>
    </div>
  );
}
