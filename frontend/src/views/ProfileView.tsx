import { useNavigate } from "react-router-dom";
import { BrutalCard as Card } from "../components/brutal/BrutalCard";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { useNavigationStore } from "../store/navigationStore";

export function ProfileView() {
  const navigate = useNavigate();
  const { profileState, assessmentProgress } = useNavigationStore();
  const rows = [
    ["Cognitive Capacity", profileState.dimensions.cognitive_capacity, "Working memory and problem-solving depth."],
    ["Attention Stability", profileState.dimensions.attention_stability, "Consistency of focus over repeated work."],
    ["Learning Tolerance", profileState.dimensions.learning_tolerance, "Ability to sustain challenge load."],
    ["Motor Baseline", profileState.dimensions.motor_baseline, "Response control and motor steadiness."],
    ["Stress Resilience", profileState.dimensions.stress_resilience, "Performance stability under pressure."],
    ["Time Constraint", profileState.dimensions.time_constraint, "Comfort operating with tight timing."],
  ] as const;

  if (!profileState.isActive) {
    return (
      <main style={{ padding: "2rem" }}>
        <Card accent="muted">
          <h1 className="headline">Profile</h1>
          <p>Profile is not ready yet. Complete all 6 assessment levels to unlock your cognitive profile.</p>
          <BrutalButton variant="primary" onClick={() => navigate("/assessment")}>
            Go to Assessment
          </BrutalButton>
        </Card>
      </main>
    );
  }

  return (
    <main style={{ padding: "2rem" }}>
      <div style={{ marginBottom: "1rem" }}>
        <h1 className="headline">Profile</h1>
      </div>
      <div className="stats-grid">
        {rows.map(([label, value, help]) => (
          <Card key={label}>
            <h2>{label}</h2>
            <p className="stat-block__value">{value.toFixed(2)}</p>
            <p className="small-copy">{help}</p>
          </Card>
        ))}
      </div>
      <Card style={{ marginTop: "1rem" }}>
        <h2>Assessment History</h2>
        <div className="recent-session-list">
          {Object.entries(assessmentProgress).map(([level, state]) => (
            <div key={level} className="recent-session-item">
              <span>Level {level}</span>
              <span>{state.status}</span>
              <span>{state.completedAt ? new Date(state.completedAt).toLocaleString() : "Not completed"}</span>
              <BrutalButton onClick={() => navigate("/assessment")} variant="secondary">
                Retake Assessment
              </BrutalButton>
            </div>
          ))}
        </div>
      </Card>
    </main>
  );
}
