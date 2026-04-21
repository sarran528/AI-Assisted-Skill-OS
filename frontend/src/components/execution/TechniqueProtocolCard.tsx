
import { BrutalCard } from "../brutal/BrutalCard";

export function TechniqueProtocolCard() {
  return (
    <div className="technique-protocol-card__container">
      <BrutalCard className="technique-protocol-card" accent="blue">
        <h2 className="technique-protocol-card__title">TECHNIQUE PROTOCOL</h2>
        <p className="technique-protocol-card__description">
          Instructions for the current session.
        </p>
      </BrutalCard>
    </div>
  );
}
