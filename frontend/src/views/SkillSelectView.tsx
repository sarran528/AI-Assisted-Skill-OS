import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { skillApi } from "../api/skillApi";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { Input } from "../components/ui/Input";
import { SerpQueryVisualization } from "../components/skill/SerpQueryVisualization";
import { RoadmapRequirementSummary } from "../components/skill/RoadmapRequirementSummary";
import { SkillContextAnalysis } from "../components/skill/SkillContextAnalysis";
import { useNavigationStore, type RoadmapPhase } from "../store/navigationStore";
import { Skill } from "../components/skill/SkillCard";
import { DynamicQuestionForm } from "../components/skill/DynamicQuestionForm";
import { type SkillAnalysis, type SkillQuestion } from "../api/skillApi";

// Pipeline stage visualization — Neo-Brutalist
const PipelineStages = ({ currentStage }: { currentStage: "idle" | "discover" | "aggregate" | "llm" | "form" | "generate" }) => {
  const stages = [
    { id: "discover",  label: "SERP",  description: "Search" },
    { id: "aggregate", label: "AGGR",  description: "Clean" },
    { id: "llm",       label: "AI",    description: "Analyse" },
    { id: "form",      label: "FORM",  description: "Inputs" },
    { id: "generate",  label: "MAP",   description: "Roadmap" },
  ];

  const order = ["idle", "discover", "aggregate", "llm", "form", "generate"];
  const currentIndex = order.indexOf(currentStage);

  return (
    <div style={{
      display: "flex",
      border: "3px solid var(--border)",
      boxShadow: "4px 4px 0 var(--shadow)",
      marginBottom: "16px",
      overflow: "hidden",
    }}>
      {stages.map((stage, idx) => {
        const stageIndex = order.indexOf(stage.id);
        const isActive   = stageIndex === currentIndex;
        const isComplete = stageIndex < currentIndex;

        return (
          <div
            key={stage.id}
            style={{
              flex: 1,
              borderRight: idx < stages.length - 1 ? "2px solid var(--border)" : "none",
              background: isActive ? "var(--color-primary)" : isComplete ? "var(--border)" : "#fff",
              padding: "10px 6px",
              textAlign: "center",
              transition: "background 0.2s",
            }}
          >
            <div style={{
              fontFamily: "var(--font-primary)",
              fontSize: "8px",
              color: isComplete ? "#fff" : isActive ? "var(--foreground)" : "#aaa",
              marginBottom: "4px",
              letterSpacing: "0.05em",
            }}>
              {stage.label}
            </div>
            <div style={{
              fontFamily: "var(--font-secondary)",
              fontSize: "9px",
              color: isComplete ? "#ccc" : isActive ? "#333" : "#bbb",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}>
              {stage.description}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export function SkillSelectView() {
  const navigate = useNavigate();
  const { profileState, currentSkill, setCurrentSkill, setRoadmapState, setRoadmapPhases, setSystemState } = useNavigationStore();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [discoverError, setDiscoverError] = useState<string | null>(null);
  const [discoverStatus, setDiscoverStatus] = useState<string | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [whyLearn, setWhyLearn] = useState("");
  const [experienceLevel, setExperienceLevel] = useState<"beginner" | "intermediate" | "advanced">("beginner");
  const [hasTools, setHasTools] = useState(true);
  const [hoursPerWeek, setHoursPerWeek] = useState(6);
  const [targetGoal, setTargetGoal] = useState<"hobby" | "professional" | "exam">("hobby");
  const [composeError, setComposeError] = useState<string | null>(null);
  const [pipelineStage, setPipelineStage] = useState<"idle" | "discover" | "aggregate" | "llm" | "form" | "generate">("idle");
  const [discoverJobId, setDiscoverJobId] = useState<string | null>(null);
  const [researchJobId, setResearchJobId] = useState<string | null>(null);
  const [skillAnalysis, setSkillAnalysis] = useState<SkillAnalysis | null>(null);
  const [skillQuestions, setSkillQuestions] = useState<SkillQuestion[]>([]);
  const [dynamicAnswers, setDynamicAnswers] = useState<Record<string, any>>({});
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    setLoading(true);
    skillApi
      .listSkills()
      .then((res: { data: Skill[] }) => {
        setSkills(res.data);
        if (currentSkill.skillId) {
          const match = res.data.find((s) => s.skill_id === currentSkill.skillId);
          if (match) setSelectedSkill(match);
        }
      })
      .catch((err) => {
        console.error("Failed to load skills:", err);
        setSkills([]);
      })
      .finally(() => setLoading(false));
  }, [currentSkill.skillId]);

  const filtered = useMemo(
    () =>
      skills.filter(
        (s) => s.name.toLowerCase().includes(search.toLowerCase()) || s.skill_id.toLowerCase().includes(search.toLowerCase())
      ),
    [search, skills]
  );

  const estimateDuration = (complexity: number) => {
    const hoursPerWeek = Math.max(2, 12 - Math.round(profileState.dimensions.time_constraint * 10));
    const totalHours = Math.max(12, complexity * 4);
    return `${Math.ceil(totalHours / hoursPerWeek)} weeks`;
  };

  const buildRoadmap = (skillName: string): RoadmapPhase[] => [
    {
      id: "phase-1",
      name: "Phase 1",
      status: "active",
      competencies: [
        {
          name: `${skillName} Foundations`,
          techniques: [
            {
              id: "tech-1",
              name: "Core Fundamentals",
              status: "active",
              checkpoints: [
                { id: "cp-1", description: "Complete fundamentals exercise", threshold: "Accuracy >= 80%", status: "pending", retriesRemaining: 3 },
                { id: "cp-2", description: "Submit foundational project", threshold: "Validation >= 70%", status: "locked", retriesRemaining: 3 },
              ],
            },
          ],
        },
      ],
    },
    {
      id: "phase-2",
      name: "Phase 2",
      status: "locked",
      competencies: [
        {
          name: `${skillName} Application`,
          techniques: [
            {
              id: "tech-2",
              name: "Applied Workflow",
              status: "locked",
              checkpoints: [{ id: "cp-3", description: "Build applied scenario", threshold: "Accuracy >= 85%", status: "locked", retriesRemaining: 3 }],
            },
          ],
        },
      ],
    },
  ];

  const onSelectSkill = async (skill: Skill) => {
    setSelectedSkill(skill);
    setCurrentSkill({ skillId: skill.skill_id, skillName: skill.name, domain: "General" });
    
    // Stage 4: Analyze skill context and get questions
    setIsAnalyzing(true);
    setPipelineStage("llm");
    try {
      const response = await skillApi.analyzeSkill(skill.name);
      setSkillAnalysis(response.data.analysis);
      setSkillQuestions(response.data.questions);
      setPipelineStage("form");
    } catch (err) {
      console.error("Analysis failed:", err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const reloadSkills = () => {
    setLoading(true);
    skillApi
      .listSkills()
      .then((res: { data: Skill[] }) => setSkills(res.data))
      .catch(() => setSkills([]))
      .finally(() => setLoading(false));
  };

  const onDiscoverSkill = async () => {
    const skillName = search.trim();
    if (!skillName) return;
    setDiscovering(true);
    setDiscoverError(null);
    setDiscoverStatus(null);
    setPipelineStage("discover");
    try {
      const response = await skillApi.discoverSkill({
        skill_name: skillName,
        domain: "other",
        complexity_score: 0.5,
      });
      const discovered: Skill = {
        skill_id: response.data.skill_id,
        name: response.data.name,
        complexity: response.data.complexity_score,
      };
      setDiscoverJobId(response.data.job_id);
      reloadSkills();
      onSelectSkill(discovered);
      setDiscoverStatus(`✓ Discovery queued (job ${response.data.job_id.slice(0, 8)}). Serp multi-query running...`);
      setPipelineStage("aggregate");
      
      // Fetch analysis after aggregation
      setTimeout(async () => {
        setPipelineStage("llm");
        const analysisRes = await skillApi.analyzeSkill(skillName);
        setSkillAnalysis(analysisRes.data.analysis);
        setSkillQuestions(analysisRes.data.questions);
        setPipelineStage("form");
      }, 1500);
    } catch (error: any) {
      setDiscoverError(error?.response?.data?.detail ?? "Could not discover skill from internet.");
      setPipelineStage("idle");
    } finally {
      setDiscovering(false);
    }
  };

  const onGenerateRoadmap = () => {
    const activeSkill = selectedSkill || (currentSkill.skillId ? { skill_id: currentSkill.skillId, name: currentSkill.skillName } : null);
    if (!activeSkill) return;

    if (!whyLearn.trim()) {
      setComposeError("Please tell us why you want to learn this skill.");
      return;
    }
    setGenerating(true);
    setComposeError(null);
    setPipelineStage("form");
    setSystemState("roadmap_generation");
    setRoadmapState({ isGenerating: true, isGenerated: false });
    skillApi.composeResearch({
      skill_id: activeSkill.skill_id as string,
      why_learn: whyLearn.trim(),
      experience_level: experienceLevel,
      has_required_tools: hasTools,
      hours_per_week: hoursPerWeek,
      target_goal: targetGoal,
      dynamic_answers: dynamicAnswers,
    }).then((response) => {
      setResearchJobId(response.data.research_job_id);
      setPipelineStage("generate");
      const phases = buildRoadmap(activeSkill.name as string);
      setRoadmapPhases(phases);
      setRoadmapState({
        isGenerating: false,
        isGenerated: true,
        currentPhase: "Phase 1",
        currentTechnique: "Core Fundamentals",
        roadmapComplete: false,
      });
      setSystemState("roadmap_active");
      navigate("/roadmap");
    }).catch((error: any) => {
      setRoadmapState({ isGenerating: false, isGenerated: false });
      setSystemState("profile_active");
      setComposeError(error?.response?.data?.detail ?? "Failed to generate research for roadmap.");
      setPipelineStage("form");
    }).finally(() => setGenerating(false));
  };

  if (!profileState.isActive) {
    return (
      <main className="main-panel main-panel--centered">
        <BrutalCard accent="red" style={{ textAlign: "center", padding: "40px" }}>
          <h1 className="headline">Access Denied</h1>
          <p style={{ marginTop: "1rem" }}>Skills are locked until your cognitive profile is finalized.</p>
          <BrutalButton variant="primary" onClick={() => navigate("/dashboard")} style={{ marginTop: "20px" }}>
            Return to Dashboard
          </BrutalButton>
        </BrutalCard>
      </main>
    );
  }

  return (
    <main className="main-panel">
      {/* Search Hero */}
      <section className="search-hero">
        <h1 className="headline" style={{ fontSize: "2.5rem" }}>What will you master?</h1>
        <p className="mono-caps" style={{ marginTop: "8px" }}>Enter any skill to discover or generate a roadmap</p>
        
        <div className="search-input-wrapper">
          <input
            className={`premium-input ${discovering ? "searching-pulse" : ""}`}
            placeholder="e.g. Quantum Computing, Watercolor Painting..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onDiscoverSkill()}
          />
          
          <div style={{ marginTop: "16px", display: "flex", justifyContent: "center", gap: "12px" }}>
            <BrutalButton 
              variant="mono" 
              onClick={onDiscoverSkill} 
              disabled={discovering || !search.trim()}
              style={{ minWidth: "200px" }}
            >
              {discovering ? "DECODING INTERNET..." : "DISCOVER SKILL"}
            </BrutalButton>
          </div>
          
          {discoverError && (
            <p className="small-copy" style={{ color: "#7a0000", marginTop: "12px", fontWeight: "bold" }}>
              ERROR: {discoverError}
            </p>
          )}
          {discoverStatus && (
            <p className="small-copy" style={{ color: "#0b4a2b", marginTop: "12px", fontWeight: "bold" }}>
              {discoverStatus}
            </p>
          )}
          {discovering && (
            <div style={{
              marginTop: "24px",
              border: "3px solid var(--border)",
              boxShadow: "6px 6px 0 var(--shadow)",
              background: "#fff",
            }}>
              {/* Title bar */}
              <div style={{
                background: "var(--color-primary)",
                borderBottom: "3px solid var(--border)",
                padding: "10px 16px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}>
                <span style={{ fontFamily: "var(--font-primary)", fontSize: "9px", letterSpacing: "0.08em" }}>
                  ► SKILL DISCOVERY PIPELINE
                </span>
                <span style={{
                  fontFamily: "var(--font-primary)",
                  fontSize: "8px",
                  border: "2px solid var(--border)",
                  padding: "2px 8px",
                  background: "var(--foreground)",
                  color: "var(--color-primary)",
                  animation: "blink-status 1s step-end infinite",
                }}>
                  ● RUNNING
                </span>
              </div>

              {/* Stage tracker */}
              <div style={{ padding: "16px 16px 0" }}>
                <PipelineStages currentStage={pipelineStage} />
              </div>

              {/* SERP grid */}
              <div style={{ padding: "0 16px" }}>
                <SerpQueryVisualization skill_name={search} isRunning={pipelineStage === "discover"} />
              </div>

              {/* Status footer */}
              <div style={{
                borderTop: "3px solid var(--border)",
                padding: "10px 16px",
                background: "var(--muted)",
                fontFamily: "'Space Mono', monospace",
                fontSize: "10px",
                color: "#444",
              }}>
                <strong>ENGINE:</strong> Analysing "{search}" — fetching roadmap patterns, prerequisites, and failure modes.
              </div>
            </div>
          )}
          <style>{`
            @keyframes blink-status {
              0%, 100% { opacity: 1; }
              50% { opacity: 0.15; }
            }
          `}</style>
        </div>
      </section>

      {/* Results Section */}
      <section style={{ padding: "0 24px 40px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "20px" }}>
          <h2 className="section-title">Available Templates {filtered.length > 0 && `(${filtered.length})`}</h2>
          {loading && <span className="small-copy">Refreshing catalog...</span>}
        </div>

        {filtered.length === 0 && !loading ? (
          <div className="empty-state" style={{ padding: "40px" }}>
            <p className="headline" style={{ opacity: 0.5 }}>No templates found</p>
            <p className="small-copy" style={{ marginTop: "8px" }}>Try searching the internet for "{search}" above.</p>
          </div>
        ) : (
          <div className="skill-grid">
            {filtered.map((skill) => (
              <div 
                key={skill.skill_id} 
                className={`brutal-card skill-card-premium ${selectedSkill?.skill_id === skill.skill_id ? "selected" : ""}`}
                onClick={() => onSelectSkill(skill)}
              >
                <span className="skill-type-tag">Template V1.0</span>
                <h3 className="font-primary" style={{ margin: "8px 0" }}>{skill.name}</h3>
                <div className="skill-card__meta">
                  <span>Complexity: {(skill.complexity * 100).toFixed(0)}%</span>
                  <span>Estimate: {estimateDuration(skill.complexity)}</span>
                </div>
                <div style={{ marginTop: "auto", paddingTop: "16px" }}>
                  <BrutalButton 
                    variant={selectedSkill?.skill_id === skill.skill_id ? "secondary" : "primary"}
                    style={{ width: "100%", fontSize: "12px" }}
                  >
                    {selectedSkill?.skill_id === skill.skill_id ? "SELECTED" : "VIEW DETAILS"}
                  </BrutalButton>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Setup Modal Overlay */}
      {(selectedSkill || currentSkill.skillId) && (
        <div className="setup-overlay" style={{ 
          backgroundColor: "rgba(0,0,0,0.85)", 
          backdropFilter: "blur(12px)",
          zIndex: 1000,
          display: "flex",
          alignItems: "center",
          justifyContent: "center"
        }}>
          <div className="setup-modal" style={{ 
            maxHeight: "90vh", 
            overflowY: "auto", 
            width: "90%", 
            maxWidth: "800px",
            backgroundColor: "var(--color-bg)",
            border: "4px solid var(--border)",
            boxShadow: "12px 12px 0 var(--shadow)",
            padding: "32px",
            position: "relative"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
              <div>
                <span className="mono-caps" style={{ color: "var(--color-tertiary)" }}>Skill Initialization</span>
                <h2 className="headline">Configuring {selectedSkill?.name || currentSkill.skillName}</h2>
              </div>
              <button 
                onClick={() => {
                  setSelectedSkill(null);
                  setCurrentSkill({ skillId: null, skillName: null, domain: null });
                  setPipelineStage("idle");
                }}
                style={{ background: "none", border: "none", cursor: "pointer", fontSize: "24px", fontWeight: "bold" }}
              >
                ×
              </button>
            </div>

            {discoverJobId && (
              <div style={{ marginBottom: "24px" }}>
                <PipelineStages currentStage={pipelineStage} />
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "10px", marginTop: "12px" }}>
                  <div className="brutal-card" style={{ padding: "8px", backgroundColor: "rgba(11, 74, 43, 0.05)" }}>
                    <span style={{ color: "#666", fontSize: "8px", textTransform: "uppercase" }}>Discovery Task</span>
                    <div style={{ fontSize: "10px", color: "#0b4a2b", fontWeight: "bold", fontFamily: "monospace" }}>{discoverJobId.slice(0, 16)}</div>
                  </div>
                  {researchJobId && (
                    <div className="brutal-card" style={{ padding: "8px", backgroundColor: "rgba(11, 74, 43, 0.05)" }}>
                      <span style={{ color: "#666", fontSize: "8px", textTransform: "uppercase" }}>Synthesis Task</span>
                      <div style={{ fontSize: "10px", color: "#0b4a2b", fontWeight: "bold", fontFamily: "monospace" }}>{researchJobId.slice(0, 16)}</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            <SkillContextAnalysis
              skillName={selectedSkill?.name || search}
              skillContext={skillAnalysis || undefined}
              isLoading={pipelineStage === "llm" || isAnalyzing}
            />

            <div className="stepper-header">
              <div className="step-dot active"></div>
              <div className={`step-dot ${whyLearn.length > 5 ? "complete" : ""}`}></div>
              <div className="step-dot"></div>
            </div>

              <div style={{ padding: "16px", backgroundColor: "rgba(255, 107, 0, 0.05)", border: "2px solid var(--border)", boxShadow: "4px 4px 0 var(--shadow)", marginBottom: "20px" }}>
                <p className="mono-caps" style={{ color: "#ff6b00", marginBottom: "12px", fontSize: "10px" }}>Stage 5: Dynamic Input Form</p>
                <DynamicQuestionForm 
                  questions={skillQuestions}
                  answers={dynamicAnswers}
                  onAnswerChange={(id, val) => setDynamicAnswers(prev => ({ ...prev, [id]: val }))}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                <div className="dashboard-value-row">
                  <label className="section-title">Experience</label>
                  <select 
                    className="brutal-input" 
                    value={experienceLevel} 
                    onChange={(e) => setExperienceLevel(e.target.value as any)}
                    style={{ width: "100%" }}
                  >
                    <option value="beginner">Newbie</option>
                    <option value="intermediate">Some knowledge</option>
                    <option value="advanced">Expert / Refresher</option>
                  </select>
                </div>

                <div className="dashboard-value-row">
                  <label className="section-title">Path Focus</label>
                  <select 
                    className="brutal-input" 
                    value={targetGoal} 
                    onChange={(e) => setTargetGoal(e.target.value as any)}
                    style={{ width: "100%" }}
                  >
                    <option value="hobby">Personal Interest</option>
                    <option value="professional">Career/Work</option>
                    <option value="exam">Academic/Test</option>
                  </select>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                <div className="dashboard-value-row">
                  <label className="section-title">Intensity (Hrs/Week)</label>
                  <input 
                    className="brutal-input" 
                    type="number" 
                    min={1} 
                    max={40} 
                    value={hoursPerWeek} 
                    onChange={(e) => setHoursPerWeek(Number(e.target.value))} 
                    style={{ width: "100%" }}
                  />
                </div>

                <div className="dashboard-value-row">
                  <label className="section-title">Resources Ready?</label>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <BrutalButton 
                      variant={hasTools ? "primary" : "secondary"} 
                      onClick={() => setHasTools(true)}
                      style={{ flex: 1, fontSize: "11px" }}
                    >
                      YES
                    </BrutalButton>
                    <BrutalButton 
                      variant={!hasTools ? "primary" : "secondary"} 
                      onClick={() => setHasTools(false)}
                      style={{ flex: 1, fontSize: "11px" }}
                    >
                      NO
                    </BrutalButton>
                  </div>
                </div>
              </div>

              {composeError && (
                <div className="brutal-card brutal-card--red" style={{ padding: "10px", fontSize: "12px" }}>
                  <strong>COMPOSER ERROR:</strong> {composeError}
                </div>
              )}

              <div style={{ padding: "12px", backgroundColor: "rgba(0, 0, 0, 0.02)", borderRadius: "4px", fontSize: "10px", color: "#666", borderLeft: "3px solid #ff6b00" }}>
                <p style={{ margin: 0, marginBottom: "6px", fontWeight: "bold", color: "#333" }}>📊 Pipeline Overview</p>
                <p style={{ margin: 0, marginBottom: "4px" }}>Your answers will be merged with the LLM-generated skill analysis to create a deterministic roadmap.</p>
                <p style={{ margin: 0 }}>Stages: SERP Research → Aggregation → LLM Analysis → Your Answers → Roadmap Generation</p>
              </div>

              {selectedSkill && whyLearn.trim() && (
                <RoadmapRequirementSummary
                  skillName={selectedSkill.name}
                  skillComplexity={selectedSkill.complexity}
                  userObjective={whyLearn}
                  experienceLevel={experienceLevel}
                  targetGoal={targetGoal}
                  hoursPerWeek={hoursPerWeek}
                  hasTools={hasTools}
                />
              )}

              <BrutalButton
                variant="primary"
                onClick={onGenerateRoadmap}
                disabled={generating}
                style={{ width: "100%", marginTop: "10px", padding: "16px" }}
              >
                {generating ? "SYNTHESIZING ROADMAP..." : "INITIALIZE ROADMAP"}
              </BrutalButton>
          </div>
        </div>
      )}
    </main>
  );
}
