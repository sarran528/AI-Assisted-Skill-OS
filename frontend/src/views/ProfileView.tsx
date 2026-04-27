import { useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { BrutalCard as Card } from "../components/brutal/BrutalCard";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { useNavigationStore } from "../store/navigationStore";
import { useAssessmentStore, GAME_IDS } from "../stores/assessmentStore";
import { useAssessmentStatus } from "../hooks/useAssessment";

export function ProfileView() {
  const navigate = useNavigate();
  const { profileState, setProfileState, setSystemState } = useNavigationStore();
  const { games } = useAssessmentStore();
  const { data: statusData } = useAssessmentStatus();

  useEffect(() => {
    if (!statusData?.profile_active || !statusData?.profile) return;

    setProfileState({
      isActive: true,
      dimensions: {
        cognitive_capacity: Number(statusData.profile.cognitive_capacity ?? 0),
        attention_stability: Number(statusData.profile.attention_stability ?? 0),
        learning_tolerance: Number(statusData.profile.learning_tolerance ?? 0),
        motor_baseline: Number(statusData.profile.motor_baseline ?? 0),
        stress_resilience: Number(statusData.profile.stress_resilience ?? 0),
        time_constraint: Number(statusData.profile.time_constraint ?? 0),
      },
      learning_parameters: statusData.learning_parameters || null,
    });
    setSystemState("profile_active");
  }, [statusData, setProfileState, setSystemState]);
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
          {GAME_IDS.map((id) => {
            const g = games[id];
            return (
              <div key={id} className="recent-session-item">
                <span>Level {id}</span>
                <span>{g.completed ? 'complete' : 'not started'}</span>
                <span>{g.completed ? `Score: ${g.bestScore}` : 'Not completed'}</span>
                <BrutalButton onClick={() => navigate("/assessment")} variant="secondary">
                  Retake Assessment
                </BrutalButton>
              </div>
            );
          })}
        </div>
      </Card>
    </main>
  );
}
