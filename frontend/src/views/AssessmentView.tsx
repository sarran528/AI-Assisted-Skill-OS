import { useNavigate } from "react-router-dom";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { useNavigationStore } from "../store/navigationStore";

const LEVELS = [
  { id: 1, name: "Executive Control", description: "Measures inhibition and impulse control." },
  { id: 2, name: "Sustained Attention", description: "Tracks focus consistency over repeated tasks." },
  { id: 3, name: "Working Memory", description: "Measures temporary information retention." },
  { id: 4, name: "Motor Baseline", description: "Checks motor speed and rhythm stability." },
  { id: 5, name: "Stress Resilience", description: "Evaluates stability under pressure." },
  { id: 6, name: "Time Constraint", description: "Measures decision quality under time limits." },
];

export function AssessmentView() {
  const navigate = useNavigate();
  const { assessmentProgress } = useNavigationStore();

  return (
    <main style={{ padding: "2rem" }}>
      <h1 className="headline" style={{ marginBottom: "1rem" }}>Assessment</h1>
      <div className="skill-grid">
        {LEVELS.map((level) => {
          const levelState = assessmentProgress[level.id];
          const isInProgress = levelState.status === "in_progress";
          const isComplete = levelState.status === "complete";
          const statusLabel = isComplete
            ? "Complete"
            : isInProgress
              ? "In Progress"
              : levelState.status === "failed"
                ? "Failed"
                : "Not Started";

          return (
            <BrutalCard key={level.id} className="skill-item">
              <div className="skill-card__header">
                <h2>{level.name}</h2>
                <p className="small-copy">{level.description}</p>
              </div>
              <span className={`status-pill status-pill--${isComplete ? "passed" : isInProgress ? "attempted" : "pending"}`}>
                {statusLabel}
              </span>
              {isInProgress && <p className="small-copy">Lives: ● ● ●</p>}
              <div className="skill-card__actions">
                {isComplete ? (
                  <span>✓</span>
                ) : (
                  <BrutalButton
                    variant="primary"
                    onClick={() => navigate(`/assessment/run/${level.id}`)}
                  >
                    {isInProgress ? "Continue" : "Start"}
                  </BrutalButton>
                )}
              </div>
            </BrutalCard>
          );
        })}
      </div>
    </main>
  );
}
