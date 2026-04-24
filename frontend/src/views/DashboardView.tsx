import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { useNavigationStore } from "../store/navigationStore";

const LEVEL_META = [
  { id: 1, name: "Executive Control", measure: "Inhibition and impulse control." },
  { id: 2, name: "Sustained Attention", measure: "Focus consistency over repeated tasks." },
  { id: 3, name: "Learning Endurance", measure: "Sustained cognitive effort tolerance." },
  { id: 4, name: "Motor Precision", measure: "Fine motor speed and control." },
  { id: 5, name: "Pressure Adaptation", measure: "Performance under stress." },
  { id: 6, name: "Time Structuring", measure: "Planning quality in time constraints." },
];

const PARAMETER_SNAPSHOT = [
  { name: "Difficulty Slope", value: "0.68", meaning: "How fast content gets harder", formula: "f(cognitive_capacity, learning_tolerance)" },
  { name: "Session Duration", value: "0.42", meaning: "Utilization of your available time", formula: "f(time_constraint, stress_resilience)" },
  { name: "Repetition Intensity", value: "0.42", meaning: "How often you repeat techniques", formula: "1 - baseline_familiarity" },
  { name: "Break Frequency", value: "0.39", meaning: "How often breaks are recommended", formula: "f(attention_stability)" },
  { name: "Feedback Detail", value: "0.26", meaning: "How detailed your feedback is", formula: "f(error_profile_variance)" },
  { name: "Retry Limit", value: "3", meaning: "Maximum retries per checkpoint", formula: "policy(profile_risk_band)" },
  { name: "Micro Sessions", value: "Off", meaning: "Short session mode not needed", formula: "time_constraint < threshold" },
  { name: "Abstraction Level", value: "0.74", meaning: "Complexity of content presented", formula: "f(cognitive_capacity)" },
];

export function DashboardView() {
  const navigate = useNavigate();
  const { assessmentProgress, profileState, currentSkill, roadmapState } = useNavigationStore();
  const [expandedSession, setExpandedSession] = useState<number | null>(null);
  const getLevelState = (id: number) =>
    assessmentProgress[id] ?? { status: "not_started" as const, attempts: 0, livesRemaining: 3 };

  const completedLevels = LEVEL_META.filter((level) => getLevelState(level.id).status === "complete").length;
  const assessmentComplete = completedLevels === 6;
  const profileActive = profileState.isActive;
  const roadmapActive = roadmapState.isGenerated;
  const activePhase = roadmapState.phases.find((phase) => phase.status === "active");
  const activePhaseIndex = roadmapState.phases.findIndex((phase) => phase.status === "active");
  const activeTechnique = activePhase?.competencies.flatMap((entry) => entry.techniques).find((technique) => technique.status === "active");
  const pendingCheckpoint = activeTechnique?.checkpoints.find((entry) => entry.status === "pending");

  const statusText = {
    assessment: `Assessment: ${assessmentComplete ? "Complete" : `${completedLevels}/6 Complete`}`,
    profile: `Profile: ${profileActive ? "Active" : "Locked"}`,
    skill:
      roadmapActive && currentSkill.skillName && activePhase
        ? `Active Skill: ${currentSkill.skillName} — Phase ${activePhaseIndex + 1} of ${roadmapState.phases.length}`
        : currentSkill.skillName
          ? `Active Skill: ${currentSkill.skillName}`
          : "No skill selected",
  };

  const profileValues = [
    ["Cognitive Capacity", profileState.dimensions.cognitive_capacity],
    ["Attention Stability", profileState.dimensions.attention_stability],
    ["Learning Tolerance", profileState.dimensions.learning_tolerance],
    ["Motor Baseline", profileState.dimensions.motor_baseline],
    ["Stress Resilience", profileState.dimensions.stress_resilience],
    ["Time Constraint", profileState.dimensions.time_constraint],
  ] as const;

  const radarPoints = profileValues
    .map(([, value], index) => {
      const angle = (Math.PI * 2 * index) / profileValues.length - Math.PI / 2;
      const radius = 90 * value;
      const x = 110 + Math.cos(angle) * radius;
      const y = 110 + Math.sin(angle) * radius;
      return `${x},${y}`;
    })
    .join(" ");

  const performanceSeries = [
    60, 62, 68, 65, 71, 73, 74, 78, 80, 82,
  ];
  const difficultySeries = [
    48, 50, 53, 55, 58, 60, 62, 64, 66, 68,
  ];
  const recentSessions = [
    { date: "23 Apr", skill: "Python", technique: "List Comprehension", result: "Pass", retries: 1, metrics: "Accuracy 84%, latency stable", evidence: "Uploaded", validation: "Passed threshold" },
    { date: "22 Apr", skill: "Python", technique: "For Loops", result: "Fail", retries: 3, metrics: "Accuracy 62%, variance high", evidence: "Uploaded", validation: "Failed accuracy >= 80%" },
    { date: "21 Apr", skill: "Python", technique: "Variables", result: "Pass", retries: 0, metrics: "Accuracy 91%, low variance", evidence: "Uploaded", validation: "Passed threshold" },
  ];

  const allQuickActions = [
    { label: "Go to Assessment", active: true, reason: "", action: () => navigate("/assessment") },
    { label: "View Full Roadmap", active: roadmapActive, reason: "Generate roadmap first", action: () => navigate("/roadmap") },
    { label: "Browse Resources", active: true, reason: "", action: () => navigate("/resources") },
    { label: "Ask Help", active: true, reason: "", action: () => navigate("/help") },
  ];

  return (
    <main className="dashboard-layout">
      <section className="dashboard-status">
        <span>{statusText.assessment}</span>
        <span>|</span>
        <span>{statusText.profile}</span>
        <span>|</span>
        <span>{statusText.skill}</span>
      </section>

      <section className="dashboard-columns">
        <div className="dashboard-left">
          <BrutalCard accent="yellow">
            <p className="section-title">ACTIVE SKILL CARD</p>
            <h2>{currentSkill.skillName ?? "No skill selected yet"}</h2>
            <p>
              {currentSkill.skillName
                ? `Focus area: ${activeTechnique?.name ?? "Roadmap generation pending"}`
                : "Finish assessment and pick a skill to unlock your roadmap."}
            </p>
            <p className="small-copy">
              {currentSkill.skillName
                ? `Current phase: ${activePhase?.name ?? "Not started"}`
                : "Progress updates will appear here after skill selection."}
            </p>
            <BrutalButton variant="primary" onClick={() => navigate(currentSkill.skillName ? "/roadmap" : "/skill/select")}>
              {currentSkill.skillName ? "Open Skill Roadmap →" : "Choose Skill →"}
            </BrutalButton>
          </BrutalCard>

          <BrutalCard>
            <h2>Assessment Progress</h2>
            <div className="dashboard-assessment-grid">
              {LEVEL_META.map((level) => {
                const state = getLevelState(level.id);
                const status = state.status === "complete" ? "Complete" : state.status === "failed" ? "Failed" : "Not Started";
                const score = (0.52 + level.id * 0.06).toFixed(2);
                return (
                  <div
                    key={level.id}
                    className={`dashboard-level-card ${state.status === "complete" ? "dashboard-level-card--complete" : ""} ${state.status === "failed" ? "dashboard-level-card--failed" : ""}`}
                  >
                    <strong>{level.name}</strong>
                    <p className="small-copy">{level.measure}</p>
                    <span className={`status-pill status-pill--${state.status === "failed" ? "failed" : state.status === "complete" ? "passed" : "pending"}`}>{status}</span>
                    {state.status === "complete" ? <p className="small-copy">Score: {score}</p> : null}
                    <p className="small-copy">
                      Lives: {[0, 1, 2].map((index) => (index < (state.livesRemaining ?? 3) ? "●" : "○")).join(" ")}
                    </p>
                  </div>
                );
              })}
            </div>
            <div className="dashboard-progress-row">
              <div className="metric-row__bar">
                <div className="metric-row__fill" style={{ width: `${(completedLevels / 6) * 100}%` }} />
              </div>
              <span className="small-copy">{completedLevels} / 6 complete</span>
              <BrutalButton variant="primary" onClick={() => navigate(`/assessment/run/${LEVEL_META.find((entry) => getLevelState(entry.id).status !== "complete")?.id ?? 1}`)} disabled={assessmentComplete}>
                {assessmentComplete ? "Assessment Complete" : "Open Assessment"}
              </BrutalButton>
            </div>
          </BrutalCard>

          <BrutalCard>
            <h2>Roadmap Progress</h2>
            {!roadmapActive ? (
              <p className="small-copy">Generate a roadmap to unlock phase tracking.</p>
            ) : (
              <div className="recent-session-list">
                {roadmapState.phases.map((phase) => {
                  const checkpoints = phase.competencies.flatMap((c) => c.techniques.flatMap((t) => t.checkpoints));
                  const passedCount = checkpoints.filter((entry) => entry.status === "passed").length;
                  return (
                    <div key={phase.id} className="confirm-box">
                      <p>
                        {phase.name}:{" "}
                        {phase.status === "complete" ? "✓ Complete" : phase.status === "active" ? `● Active (${passedCount} of ${checkpoints.length} checkpoints passed)` : "○ Locked"}
                      </p>
                      {phase.status === "active" ? (
                        <div className="small-copy">
                          {phase.competencies.flatMap((c) => c.techniques).map((technique) => (
                            <div key={technique.id} style={{ marginTop: "6px" }}>
                              <strong>{technique.name}</strong> — {technique.status}
                              {technique.checkpoints.map((checkpoint) => (
                                <div key={checkpoint.id} style={{ display: "flex", justifyContent: "space-between", gap: "6px" }}>
                                  <span>{checkpoint.description} ({checkpoint.status})</span>
                                  {checkpoint.status === "pending" ? (
                                    <BrutalButton onClick={() => navigate("/roadmap")}>Upload Evidence</BrutalButton>
                                  ) : null}
                                </div>
                              ))}
                            </div>
                          ))}
                          <p style={{ marginTop: "8px" }}>{passedCount} / {checkpoints.length} checkpoints complete</p>
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            )}
          </BrutalCard>

          <BrutalCard>
            <h2>Recent Session History</h2>
            {!roadmapActive ? (
              <p className="small-copy">Complete roadmap generation to unlock session history.</p>
            ) : (
              <div className="dashboard-table">
                <div className="dashboard-table__header">
                  <span>Date</span><span>Skill</span><span>Technique</span><span>Result</span><span>Retries Used</span>
                </div>
                {recentSessions.slice(0, 5).map((row, index) => (
                  <div key={`${row.date}-${row.technique}`}>
                    <button className="dashboard-table__row" onClick={() => setExpandedSession(expandedSession === index ? null : index)}>
                      <span>{row.date}</span><span>{row.skill}</span><span>{row.technique}</span><span>{row.result}</span><span>{row.retries}</span>
                    </button>
                    {expandedSession === index ? (
                      <div className="dashboard-row-expand small-copy">
                        <p>Metrics captured: {row.metrics}</p>
                        <p>Evidence submitted: {row.evidence}</p>
                        <p>Validation detail: {row.validation}</p>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </BrutalCard>
        </div>

        <div className="dashboard-right">
          <BrutalCard>
            <h2>Profile Vector Radar Chart</h2>
            <div className="dashboard-radar-wrap">
              <svg width="220" height="220" viewBox="0 0 220 220">
                {[0.2, 0.4, 0.6, 0.8, 1].map((ring) => {
                  const points = profileValues
                    .map((_, index) => {
                      const angle = (Math.PI * 2 * index) / profileValues.length - Math.PI / 2;
                      const radius = 90 * ring;
                      return `${110 + Math.cos(angle) * radius},${110 + Math.sin(angle) * radius}`;
                    })
                    .join(" ");
                  return <polygon key={ring} points={points} fill="none" stroke="#999" strokeWidth="1" />;
                })}
                <polygon points={radarPoints} fill={profileActive ? "rgba(245,200,0,0.45)" : "rgba(180,180,180,0.35)"} stroke="#0a0a0a" strokeWidth="2" />
              </svg>
              {!profileActive ? <div className="dashboard-locked-overlay">Complete assessment to unlock</div> : null}
            </div>
            <div className="recent-session-list">
              {profileValues.map(([label, value]) => (
                <div key={label} className="dashboard-value-row">
                  <span>{label}</span>
                  <span>{value.toFixed(2)}</span>
                  <div className="metric-row__bar"><div className="metric-row__fill" style={{ width: `${value * 100}%` }} /></div>
                </div>
              ))}
            </div>
          </BrutalCard>

          <BrutalCard>
            <h2>Learning Parameter Snapshot</h2>
            {!profileActive ? (
              <p className="small-copy">Complete assessment to unlock learning parameters.</p>
            ) : (
              <div className="dashboard-table">
                <div className="dashboard-table__header">
                  <span>Parameter</span><span>Value</span><span>What it means</span>
                </div>
                {PARAMETER_SNAPSHOT.map((item) => (
                  <div className="dashboard-table__row dashboard-table__row--3" key={item.name}>
                    <span title={item.formula}>{item.name} ⓘ</span>
                    <span>{item.value}</span>
                    <span>{item.meaning}</span>
                  </div>
                ))}
              </div>
            )}
          </BrutalCard>

          <BrutalCard>
            <h2>Performance Trend Chart</h2>
            {!roadmapActive ? (
              <p className="small-copy">Generate roadmap and complete sessions to unlock trend analytics.</p>
            ) : performanceSeries.length < 3 ? (
              <p className="small-copy">More sessions needed to show trend.</p>
            ) : (
              <svg width="100%" height="160" viewBox="0 0 360 160">
                <polyline
                  fill="none"
                  stroke="#0a0a0a"
                  strokeWidth="2"
                  points={performanceSeries.map((value, index) => `${20 + index * 34},${140 - value}`).join(" ")}
                />
                <polyline
                  fill="none"
                  stroke="#777"
                  strokeDasharray="5 4"
                  strokeWidth="2"
                  points={difficultySeries.map((value, index) => `${20 + index * 34},${140 - value}`).join(" ")}
                />
              </svg>
            )}
          </BrutalCard>

          <BrutalCard>
            <h2>Time Analytics</h2>
            <div className="dashboard-metric-tiles">
              <div className="stat-block"><div className="stat-block__label">Total Hours Invested</div><div className="stat-block__value">{roadmapActive ? "14.5 hrs" : "2.1 hrs"}</div></div>
              <div className="stat-block"><div className="stat-block__label">Avg Session Length</div><div className="stat-block__value">{roadmapActive ? "42 min" : "18 min"}</div></div>
              <div className="stat-block"><div className="stat-block__label">Sessions This Week</div><div className="stat-block__value">{roadmapActive ? "3" : "1"}</div></div>
            </div>
            <div className="recent-session-list small-copy">
              {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, index) => {
                const count = [2, 0, 3, 1, 0, 0, 2][index];
                return (
                  <div key={day} className="dashboard-day-row">
                    <span>{day}</span>
                    <span>{count > 0 ? "█".repeat(count) : "░"}</span>
                  </div>
                );
              })}
            </div>
          </BrutalCard>

          <BrutalCard>
            <h2>Quick Access</h2>
            <div className="recent-session-list">
              {allQuickActions.map((item) => (
                <BrutalButton
                  key={item.label}
                  variant={item.active ? "primary" : "secondary"}
                  disabled={!item.active}
                  title={!item.active ? item.reason : undefined}
                  onClick={item.action}
                >
                  {item.label}
                </BrutalButton>
              ))}
            </div>
          </BrutalCard>
        </div>
      </section>
    </main>
  );
}
