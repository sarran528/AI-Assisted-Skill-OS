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

  return (
    <div style={{ backgroundColor: "rgba(11, 74, 43, 0.03)", borderRadius: "4px", border: "1px solid rgba(11, 74, 43, 0.2)", padding: "12px" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "10px" }}>
        {/* Column 1: Skill Context */}
        <div>
          <p style={{ margin: "0 0 8px", fontWeight: "bold", color: "#0b4a2b", fontSize: "9px", textTransform: "uppercase" }}>
            📊 Skill Context
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px", color: "#666" }}>
            <div>
              <span style={{ fontWeight: "bold", color: "#333" }}>Skill:</span> {skillName}
            </div>
            <div>
              <span style={{ fontWeight: "bold", color: "#333" }}>Complexity:</span>{" "}
              <span style={{ color: "#ff6b00", fontWeight: "bold" }}>
                {(skillComplexity * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              <span style={{ fontWeight: "bold", color: "#333" }}>Est. Duration:</span> ~{estimatedWeeks} weeks
            </div>
          </div>
        </div>

        {/* Column 2: User Context */}
        <div>
          <p style={{ margin: "0 0 8px", fontWeight: "bold", color: "#0b4a2b", fontSize: "9px", textTransform: "uppercase" }}>
            👤 User Context
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px", color: "#666" }}>
            <div>
              <span style={{ fontWeight: "bold", color: "#333" }}>Experience:</span> {experienceLevel}
            </div>
            <div>
              <span style={{ fontWeight: "bold", color: "#333" }}>Pace:</span> {difficultyAdjustment}
            </div>
            <div>
              <span style={{ fontWeight: "bold", color: "#333" }}>Goal:</span> {targetGoal}
            </div>
          </div>
        </div>
      </div>

      {/* Objective */}
      <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid rgba(11, 74, 43, 0.1)" }}>
        <p style={{ margin: "0 0 6px", fontWeight: "bold", color: "#0b4a2b", fontSize: "9px", textTransform: "uppercase" }}>
          🎯 Your Objective
        </p>
        <p style={{ margin: 0, color: "#666", fontSize: "9px", lineHeight: "1.4", fontStyle: "italic" }}>
          "{userObjective}"
        </p>
      </div>

      {/* Constraints */}
      <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid rgba(11, 74, 43, 0.1)" }}>
        <p style={{ margin: "0 0 6px", fontWeight: "bold", color: "#0b4a2b", fontSize: "9px", textTransform: "uppercase" }}>
          ⚙️ Roadmap Constraints
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: "6px", fontSize: "8px" }}>
          <div
            style={{
              padding: "6px",
              backgroundColor: "rgba(11, 74, 43, 0.05)",
              borderRadius: "3px",
              border: "1px solid rgba(11, 74, 43, 0.1)",
            }}
          >
            <div style={{ fontWeight: "bold", color: "#0b4a2b", marginBottom: "2px" }}>Weekly Hours</div>
            <div style={{ color: "#666" }}>{hoursPerWeek} hrs/wk</div>
          </div>
          <div
            style={{
              padding: "6px",
              backgroundColor: "rgba(11, 74, 43, 0.05)",
              borderRadius: "3px",
              border: "1px solid rgba(11, 74, 43, 0.1)",
            }}
          >
            <div style={{ fontWeight: "bold", color: "#0b4a2b", marginBottom: "2px" }}>Resources</div>
            <div style={{ color: "#666" }}>{hasTools ? "Ready ✓" : "Needed"}</div>
          </div>
          <div
            style={{
              padding: "6px",
              backgroundColor: "rgba(11, 74, 43, 0.05)",
              borderRadius: "3px",
              border: "1px solid rgba(11, 74, 43, 0.1)",
            }}
          >
            <div style={{ fontWeight: "bold", color: "#0b4a2b", marginBottom: "2px" }}>Pace</div>
            <div style={{ color: "#666" }}>{difficultyAdjustment}</div>
          </div>
        </div>
      </div>

      <p style={{ fontSize: "8px", margin: "12px 0 0", color: "#999", fontStyle: "italic" }}>
        These constraints will be used to generate a deterministic, personalized learning roadmap.
      </p>
    </div>
  );
}
