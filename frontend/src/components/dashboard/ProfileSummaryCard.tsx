
import { BrutalCard } from "../brutal/BrutalCard";

export function ProfileSummaryCard() {
  return (
    <div className="profile-summary-card__container">
      <BrutalCard className="profile-summary-card" accent="blue">
        <h2 className="profile-summary-card__title">PROFILE SUMMARY</h2>
        <p className="profile-summary-card__description">
          Your cognitive profile at a glance.
        </p>
      </BrutalCard>
    </div>
  );
}
