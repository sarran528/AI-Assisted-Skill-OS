/**
 * Roadmap Requirement Summary Component
 * 
 * Visualizes the final RoadmapRequirementObject that's being constructed.
 * Shows:
 * - Skill Context (from LLM analysis + SERP data)
 * - User Answers (from the form)
 * - Roadmap Constraints (merged result)
 */

export interface RoadmapRequirementSummaryProps {
  skillName: string;
  skillComplexity: number;
  userObjective: string;
  experienceLevel: "beginner" | "intermediate" | "advanced";
  targetGoal: "hobby" | "professional" | "exam";
  hoursPerWeek: number;
  hasTools: boolean;
  showDetails?: boolean;
}

export function RoadmapRequirementSummary(props: RoadmapRequirementSummaryProps) {
  const {
    skillName,
    skillComplexity,
    userObjective,
    experienceLevel,
    targetGoal,
    hoursPerWeek,
    hasTools,
    showDetails = false,
  } = props;

  const estimatedWeeks = Math.ceil((skillComplexity * 100) / Math.max(5, hoursPerWeek));
  const difficultyAdjustment = (
    hoursPerWeek >= 10 ? "accelerated" :
    hoursPerWeek >= 6 ? "standard" :
    "extended"
  );
  const weeklyLoad = hoursPerWeek >= 12 ? "High" : hoursPerWeek >= 6 ? "Balanced" : "Light";
  const goalLabel = targetGoal === "professional" ? "Career" : targetGoal === "exam" ? "Exam" : "Personal";
  const toolsLabel = hasTools ? "Ready" : "Need Setup";

  return (
    <div
      style={{
        border: "3px solid var(--border)",
        boxShadow: "4px 4px 0 var(--shadow)",
        background: "#fff",
        padding: "14px",
        marginBottom: "12px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
        <p className="section-title" style={{ margin: 0 }}>Roadmap Input Summary</p>
        <span className="mono-caps" style={{ fontSize: "10px" }}>Stage: Ready To Generate</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
        <div className="confirm-box" style={{ marginTop: 0 }}>
          <p className="mono-caps" style={{ margin: "0 0 8px 0" }}>Skill Context</p>
          <p style={{ margin: "0 0 6px 0" }}><strong>Skill:</strong> {skillName}</p>
          <p style={{ margin: "0 0 6px 0" }}><strong>Complexity:</strong> {(skillComplexity * 100).toFixed(0)}%</p>
          <p style={{ margin: 0 }}><strong>Estimated:</strong> ~{estimatedWeeks} weeks</p>
        </div>
        <div className="confirm-box" style={{ marginTop: 0 }}>
          <p className="mono-caps" style={{ margin: "0 0 8px 0" }}>Learning Profile</p>
          <p style={{ margin: "0 0 6px 0" }}><strong>Experience:</strong> {experienceLevel}</p>
          <p style={{ margin: "0 0 6px 0" }}><strong>Pace:</strong> {difficultyAdjustment}</p>
          <p style={{ margin: 0 }}><strong>Goal:</strong> {goalLabel}</p>
        </div>
      </div>

      <div className="confirm-box" style={{ marginTop: 0 }}>
        <p className="mono-caps" style={{ margin: "0 0 8px 0" }}>Objective</p>
        <p style={{ margin: 0, lineHeight: 1.4 }}>
          "{userObjective}"
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: "8px", marginTop: "10px" }}>
        <div className="stat-block" style={{ padding: "8px" }}>
          <p className="mono-caps" style={{ margin: "0 0 4px 0", fontSize: "10px" }}>Hours/Week</p>
          <p style={{ margin: 0, fontWeight: 700 }}>{hoursPerWeek}</p>
        </div>
        <div className="stat-block" style={{ padding: "8px" }}>
          <p className="mono-caps" style={{ margin: "0 0 4px 0", fontSize: "10px" }}>Load</p>
          <p style={{ margin: 0, fontWeight: 700 }}>{weeklyLoad}</p>
        </div>
        <div className="stat-block" style={{ padding: "8px" }}>
          <p className="mono-caps" style={{ margin: "0 0 4px 0", fontSize: "10px" }}>Resources</p>
          <p style={{ margin: 0, fontWeight: 700 }}>{toolsLabel}</p>
        </div>
        <div className="stat-block" style={{ padding: "8px" }}>
          <p className="mono-caps" style={{ margin: "0 0 4px 0", fontSize: "10px" }}>Mode</p>
          <p style={{ margin: 0, fontWeight: 700 }}>{difficultyAdjustment}</p>
        </div>
      </div>
    </div>
  );
}
