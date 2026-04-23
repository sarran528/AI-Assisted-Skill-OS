import { useNavigate } from "react-router-dom";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { useNavigationStore } from "../store/navigationStore";

export function DashboardView() {
  const navigate = useNavigate();
  const { assessmentProgress, profileState } = useNavigationStore();
  const completedLevels = Object.values(assessmentProgress).filter((level) => level.status === "complete").length;
  const assessmentComplete = completedLevels === 6;

  return (
    <main style={{ padding: "2rem" }}>
      {!assessmentComplete ? (
        <BrutalCard className="dashboard-card" accent="yellow">
          <h1 className="headline">Welcome to SkillOS</h1>
          <p>Complete the 6-level assessment to activate your learning profile.</p>
          <BrutalButton variant="primary" onClick={() => navigate("/assessment")}>
            Go to Assessment
          </BrutalButton>
        </BrutalCard>
      ) : (
        <BrutalCard className="dashboard-card">
          <h1 className="headline">Profile Summary</h1>
          <div className="stats-grid">
            <div className="stat-block"><div className="stat-block__label">Cognitive Capacity</div><div className="stat-block__value">{profileState.dimensions.cognitive_capacity.toFixed(2)}</div></div>
            <div className="stat-block"><div className="stat-block__label">Attention Stability</div><div className="stat-block__value">{profileState.dimensions.attention_stability.toFixed(2)}</div></div>
            <div className="stat-block"><div className="stat-block__label">Learning Tolerance</div><div className="stat-block__value">{profileState.dimensions.learning_tolerance.toFixed(2)}</div></div>
            <div className="stat-block"><div className="stat-block__label">Motor Baseline</div><div className="stat-block__value">{profileState.dimensions.motor_baseline.toFixed(2)}</div></div>
            <div className="stat-block"><div className="stat-block__label">Stress Resilience</div><div className="stat-block__value">{profileState.dimensions.stress_resilience.toFixed(2)}</div></div>
            <div className="stat-block"><div className="stat-block__label">Time Constraint</div><div className="stat-block__value">{profileState.dimensions.time_constraint.toFixed(2)}</div></div>
          </div>
          <p>Your profile is active. Select a skill to begin learning.</p>
          <BrutalButton variant="primary" onClick={() => navigate("/skill/select")}>
            Browse Skills
          </BrutalButton>
        </BrutalCard>
      )}
    </main>
  );
}
