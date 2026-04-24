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
  const getLevelState = (id: number) =>
    assessmentProgress[id] ?? { status: "not_started" as const, attempts: 0, livesRemaining: 3 };
  const completedCount = LEVELS.filter((level) => getLevelState(level.id).status === "complete").length;
  const activeLevel = LEVELS.find((level) => getLevelState(level.id).status !== "complete") ?? null;
  const actionLabel = !activeLevel
    ? "Assessment Complete"
    : assessmentProgress[activeLevel.id].status === "failed"
      ? `Retry Level ${activeLevel.id}`
      : assessmentProgress[activeLevel.id].status === "in_progress"
        ? `Continue Level ${activeLevel.id}`
        : `Start Level ${activeLevel.id}`;

  return (
    <main style={{ padding: "2rem" }}>
      <h1 className="headline" style={{ marginBottom: "1rem" }}>Assessment</h1>
      <BrutalCard className="skill-item" style={{ marginBottom: "1rem" }}>
        <h2>Assessment Progress</h2>
        <p className="small-copy">{completedCount} / 6 levels complete</p>
        <div className="metric-row__bar" aria-label="Assessment completion progress">
          <div className="metric-row__fill" style={{ width: `${(completedCount / 6) * 100}%` }} />
        </div>
        <div className="skill-card__actions">
          <BrutalButton
            variant="primary"
            disabled={!activeLevel}
            onClick={() => activeLevel && navigate(`/assessment/run/${activeLevel.id}`)}
          >
            {actionLabel}
          </BrutalButton>
        </div>
      </BrutalCard>
      <div className="skill-grid">
        {LEVELS.map((level) => {
          const levelState = getLevelState(level.id);
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
              <p className="small-copy">
                Lives: {[0, 1, 2].map((index) => (index < (levelState.livesRemaining ?? 3) ? "●" : "○")).join(" ")}
              </p>
              <div className="skill-card__actions">
                {isComplete ? <span>✓ Complete</span> : <span className="small-copy">Launch from the progress card above</span>}
              </div>
            </BrutalCard>
          );
        })}
      </div>
    </main>
  );
}
