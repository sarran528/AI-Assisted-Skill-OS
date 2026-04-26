import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { useNavigationStore } from "../store/navigationStore";
import { useAssessmentStore, GAME_IDS } from "../stores/assessmentStore";

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
  const { profileState, currentSkill, roadmapState } = useNavigationStore();
  const { games } = useAssessmentStore();
  const [expandedSession, setExpandedSession] = useState<number | null>(null);

  const getLevelState = (id: number) => {
    const g = games[id as keyof typeof games];
    return { status: g && g.completed ? 'complete' as const : 'not_started' as const, attempts: g?.attempts ?? 0, livesRemaining: g?.lastLivesRemaining ?? 3 };
  };

  const completedLevels = GAME_IDS.filter(id => games[id].completed).length;
  const assessmentComplete = completedLevels === 6;
  const profileActive = profileState.isActive;
  const roadmapActive = roadmapState.isGenerated;
  const activePhase = roadmapState.phases.find((phase) => phase.status === "active");
  const activePhaseIndex = roadmapState.phases.findIndex((phase) => phase.status === "active");
  const activeTechnique = activePhase?.competencies.flatMap((entry) => entry.techniques).find((technique) => technique.status === "active");

  const profileValues: Array<[string, number]> = [
    ["Cognitive Capacity", profileState.dimensions.cognitive_capacity],
    ["Attention Stability", profileState.dimensions.attention_stability],
    ["Learning Tolerance", profileState.dimensions.learning_tolerance],
    ["Motor Baseline", profileState.dimensions.motor_baseline],
    ["Stress Resilience", profileState.dimensions.stress_resilience],
    ["Time Constraint", profileState.dimensions.time_constraint],
  ];

  // Radar points for the main profile
  const radarPoints = profileValues
    .map(([, value], index) => {
      const angle = (Math.PI * 2 * index) / profileValues.length - Math.PI / 2;
      const radius = 90 * value;
      const x = 110 + Math.cos(angle) * radius;
      const y = 110 + Math.sin(angle) * radius;
      return `${x},${y}`;
    })
    .join(" ");

  // Mapping for parameter display
  const getDisplayParams = () => {
    const p = profileState.learning_parameters;
    if (!p) return PARAMETER_SNAPSHOT; // Fallback
    
    return [
      { name: "Difficulty Slope", value: p.difficulty_slope?.toFixed(2) ?? "0.00", meaning: "Speed of complexity increase" },
      { name: "Session Duration", value: p.session_duration?.toFixed(2) ?? "0.00", meaning: "Recommended block length" },
      { name: "Repetition Intensity", value: p.repetition_intensity?.toFixed(2) ?? "0.00", meaning: "Drill repetition count" },
      { name: "Break Frequency", value: p.break_frequency?.toFixed(2) ?? "0.00", meaning: "Intervals between rests" },
      { name: "Feedback Detail", value: p.feedback_detail_level?.toFixed(2) ?? "0.00", meaning: "Granularity of error info" },
      { name: "Retry Limit", value: p.retry_limit ?? "0", meaning: "Max attempts before reset" },
      { name: "Abstraction Level", value: p.abstraction_level?.toFixed(2) ?? "0.00", meaning: "Conceptual vs Concrete" },
      { name: "Stress Exposure", value: p.stress_exposure_rate?.toFixed(2) ?? "0.00", meaning: "Introduction of constraints" },
    ];
  };

  const currentParams = getDisplayParams();

  return (
    <main className="dashboard-layout">
      <section className="dashboard-status">
        <span>Assessment: {assessmentComplete ? "Complete" : `${completedLevels}/6 Complete`}</span>
        <span>|</span>
        <span>Profile: {profileActive ? "Active" : "Locked"}</span>
        <span>|</span>
        <span>Skill: {currentSkill.skillName ?? "Not selected"}</span>
      </section>

      <section className="dashboard-columns">
        <div className="dashboard-left">
          {/* Main Skill Card */}
          <BrutalCard accent="yellow">
            <p className="section-title">ACTIVE SKILL PATH</p>
            <h2 style={{ fontSize: '2.5rem', margin: '0.5rem 0' }}>{currentSkill.skillName ?? "Ready for Skill Selection"}</h2>
            <p style={{ fontSize: '1.2rem' }}>
              {currentSkill.skillName
                ? `Focus: ${activeTechnique?.name ?? "Building roadmap..."}`
                : "Your cognitive profile is ready. Pick a skill to see your personalized path."}
            </p>
            <BrutalButton variant="primary" onClick={() => navigate(currentSkill.skillName ? "/roadmap" : "/skill/select")} style={{ marginTop: '1.5rem' }}>
              {currentSkill.skillName ? "Resume Learning →" : "Pick a Skill →"}
            </BrutalButton>
          </BrutalCard>

          {/* New: Dimension Stability Bars */}
          <BrutalCard>
            <h2 style={{ marginBottom: '1.5rem' }}>Dimension Stability Analysis</h2>
            <div className="recent-session-list">
              {profileValues.map(([label, value]) => (
                <div key={label} style={{ marginBottom: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 900 }}>{label.toUpperCase()}</span>
                    <span>{(value * 100).toFixed(0)}%</span>
                  </div>
                  <div className="metric-row__bar" style={{ height: '14px' }}>
                    <div 
                      className="metric-row__fill" 
                      style={{ 
                        width: `${value * 100}%`, 
                        background: value > 0.7 ? '#22C55E' : value > 0.4 ? '#F59E0B' : '#EF4444',
                        transition: 'width 1s ease-out'
                      }} 
                    />
                  </div>
                </div>
              ))}
            </div>
          </BrutalCard>

          {/* Assessment Overview */}
          <BrutalCard>
            <h2>Assessment Battery</h2>
            <div className="dashboard-assessment-grid">
              {LEVEL_META.map((level) => {
                const state = getLevelState(level.id);
                return (
                  <div key={level.id} className={`dashboard-level-card ${state.status === "complete" ? "dashboard-level-card--complete" : ""}`}>
                    <strong>{level.name}</strong>
                    <div style={{ fontSize: '1.5rem', margin: '8px 0' }}>
                      {Array.from({ length: 3 }).map((_, i) => (i < state.livesRemaining ? '●' : '○')).join(' ')}
                    </div>
                    <span className={`status-pill status-pill--${state.status === "complete" ? "passed" : "pending"}`}>
                      {state.status === "complete" ? "READY" : "LOCKED"}
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="dashboard-progress-row" style={{ marginTop: '2rem' }}>
              <BrutalButton variant="secondary" onClick={() => navigate("/assessment")} style={{ width: '100%' }}>
                Re-take Assessment Suite →
              </BrutalButton>
            </div>
          </BrutalCard>
        </div>

        <div className="dashboard-right">
          {/* Radar Chart Card */}
          <BrutalCard>
            <h2>Cognitive Profile Radar</h2>
            <div className="dashboard-radar-wrap" style={{ position: 'relative', margin: '2rem 0', display: 'flex', justifyContent: 'center' }}>
              <svg width="280" height="280" viewBox="0 0 280 280">
                {/* Background Rings */}
                {[0.2, 0.4, 0.6, 0.8, 1].map((ring) => {
                  const points = profileValues
                    .map((_, index) => {
                      const angle = (Math.PI * 2 * index) / profileValues.length - Math.PI / 2;
                      const radius = 100 * ring;
                      return `${140 + Math.cos(angle) * radius},${140 + Math.sin(angle) * radius}`;
                    })
                    .join(" ");
                  return <polygon key={ring} points={points} fill="none" stroke="#ddd" strokeWidth="1" />;
                })}
                {/* Labels */}
                {profileValues.map(([label], index) => {
                  const angle = (Math.PI * 2 * index) / profileValues.length - Math.PI / 2;
                  const x = 140 + Math.cos(angle) * 120;
                  const y = 140 + Math.sin(angle) * 120;
                  return (
                    <text 
                      key={label} 
                      x={x} 
                      y={y} 
                      fontSize="10" 
                      fontWeight="900" 
                      textAnchor="middle" 
                      alignmentBaseline="middle"
                      fill="#000"
                    >
                      {label.split(' ')[0].toUpperCase()}
                    </text>
                  );
                })}
                {/* Data Polygon */}
                <polygon 
                  points={profileValues
                    .map(([, value], index) => {
                      const angle = (Math.PI * 2 * index) / profileValues.length - Math.PI / 2;
                      const radius = 100 * value;
                      return `${140 + Math.cos(angle) * radius},${140 + Math.sin(angle) * radius}`;
                    })
                    .join(" ")} 
                  fill={profileActive ? "rgba(255, 229, 0, 0.7)" : "rgba(200, 200, 200, 0.2)"} 
                  stroke="#000" 
                  strokeWidth="3" 
                />
              </svg>
              {!profileActive && <div className="dashboard-locked-overlay">COMPLETE ASSESSMENT TO UNLOCK</div>}
            </div>
            
            {/* New: Cognitive Footprint Gauge */}
            <div style={{ background: '#000', color: '#fff', padding: '1rem', marginTop: '1rem', textAlign: 'center' }}>
              <p style={{ fontSize: '0.7rem', letterSpacing: '2px', margin: 0 }}>COGNITIVE FOOTPRINT</p>
              <h1 style={{ fontSize: '3rem', margin: 0 }}>
                {((profileValues.reduce((acc, [, v]) => acc + v, 0) / 6) * 100).toFixed(0)}%
              </h1>
            </div>
            
            {/* New: Dimension Comparison Bars */}
            <div className="recent-session-list" style={{ borderTop: '4px solid #000', paddingTop: '1.5rem' }}>
              <p className="small-copy" style={{ fontWeight: 900, marginBottom: '1rem' }}>TOP STRENGTHS</p>
              {[...profileValues].sort((a, b) => b[1] - a[1]).slice(0, 3).map(([label, value]) => (
                <div key={label} className="dashboard-value-row">
                  <span style={{ fontSize: '0.8rem' }}>{label}</span>
                  <span style={{ fontWeight: 900 }}>{(value * 10).toFixed(1)}</span>
                </div>
              ))}
            </div>
          </BrutalCard>

          {/* Learning Parameters Card */}
          <BrutalCard accent="blue">
            <h2>Optimal Learning Engine</h2>
            {!profileActive ? (
              <p className="small-copy">Assessment required to calibrate learning engine.</p>
            ) : (
              <div className="dashboard-table">
                <div className="dashboard-table__header" style={{ background: '#000', color: '#fff' }}>
                  <span>PARAMETER</span><span>VALUE</span><span>ACTION</span>
                </div>
                {currentParams.map((item) => (
                  <div className="dashboard-table__row dashboard-table__row--3" key={item.name} style={{ borderBottom: '2px solid #000' }}>
                    <span style={{ fontWeight: 900 }}>{item.name}</span>
                    <span style={{ fontFamily: 'monospace', fontSize: '1.1rem' }}>{item.value}</span>
                    <span className="small-copy">{item.meaning}</span>
                  </div>
                ))}
              </div>
            )}
          </BrutalCard>

          {/* New: Quick Action Terminal */}
          <BrutalCard>
            <h2>System Controls</h2>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <BrutalButton variant="primary" onClick={() => navigate("/roadmap")}>VIEW ROADMAP</BrutalButton>
              <BrutalButton variant="secondary" onClick={() => navigate("/skill/select")}>SWITCH SKILL</BrutalButton>
              <BrutalButton variant="mono" onClick={() => navigate("/resources")}>RESOURCES</BrutalButton>
              <BrutalButton variant="danger" onClick={() => navigate("/help")}>GET HELP</BrutalButton>
            </div>
          </BrutalCard>
        </div>
      </section>
    </main>
  );
}
