import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { skillApi } from "../api/skillApi";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { SimplifiedDiscoveryForm } from "../components/skill/SimplifiedDiscoveryForm";
import { ProgressBar } from "../components/skill/ProgressBar";
import { RoadmapRequirementSummary } from "../components/skill/RoadmapRequirementSummary";
import { useNavigationStore, type RoadmapPhase } from "../store/navigationStore";
import { Skill } from "../components/skill/SkillCard";
import { DynamicQuestionForm } from "../components/skill/DynamicQuestionForm";
import { type SkillQuestion } from "../api/skillApi";


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

  const onDiscoverSkill = async (skillName: string) => {
    if (!skillName.trim()) return;
    setSearch(skillName);
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

  const onOpenRoadmap = (skill: Skill) => {
    setSelectedSkill(skill);
    setCurrentSkill({ skillId: skill.skill_id, skillName: skill.name, domain: "General" });
    const phases = buildRoadmap(skill.name);
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
  };

  // Lock body scroll when modal is open
  useEffect(() => {
    const isOpen = !!(selectedSkill || currentSkill.skillId);
    document.body.style.overflow = isOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [selectedSkill, currentSkill.skillId]);

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
      <section style={{ padding: "24px 24px 0" }}>
        <SimplifiedDiscoveryForm
          onSubmit={onDiscoverSkill}
          isLoading={discovering}
          error={discoverError}
        />

        {discovering && (
          <div style={{ marginTop: "12px" }}>
            <ProgressBar currentStage={pipelineStage} isLoading={discovering} />
          </div>
        )}

        {discoverStatus && (
          <div
            style={{
              border: "2px solid var(--border)",
              color: "var(--foreground)",
              background: "var(--accent-green)",
              padding: "10px 12px",
              marginTop: "12px",
              fontFamily: "var(--font-secondary)",
              fontSize: "12px",
              boxShadow: "3px 3px 0 var(--shadow)",
            }}
          >
            {discoverStatus}
          </div>
        )}
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
                <div style={{ marginTop: "auto", paddingTop: "16px", display: "grid", gap: "8px" }}>
                  <BrutalButton 
                    variant={selectedSkill?.skill_id === skill.skill_id ? "secondary" : "primary"}
                    style={{ width: "100%", fontSize: "12px" }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectSkill(skill);
                    }}
                  >
                    {selectedSkill?.skill_id === skill.skill_id ? "SELECTED" : "VIEW DETAILS"}
                  </BrutalButton>
                  <BrutalButton
                    variant="mono"
                    style={{ width: "100%", fontSize: "12px" }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenRoadmap(skill);
                    }}
                  >
                    OPEN ROADMAP
                  </BrutalButton>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {(selectedSkill || currentSkill.skillId) && (
        <div className="setup-overlay" style={{ 
          backgroundColor: "#000",
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
            backgroundColor: "var(--background)",
            border: "4px solid var(--border)",
            boxShadow: "12px 12px 0 var(--shadow)",
            padding: "32px",
            position: "relative"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "19px" }}>
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
                <ProgressBar currentStage={pipelineStage} isLoading={pipelineStage !== "idle"} />
              </div>
            )}

            {(pipelineStage === "llm" || isAnalyzing) && (
              <div className="brutal-card brutal-card--muted" style={{ marginBottom: "16px" }}>
                <p className="mono-caps" style={{ margin: 0 }}>Preparing your setup form...</p>
              </div>
            )}

            <div className="dashboard-value-row" style={{ marginBottom: "16px" }}>
              <label className="section-title">Why do you want to learn this?</label>
              <textarea
                className="brutal-input brutal-input--textarea"
                value={whyLearn}
                onChange={(e) => setWhyLearn(e.target.value)}
                rows={4}
                placeholder="Example: I want to improve communication at work."
                style={{ width: "100%" }}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
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
                <label className="section-title">Focus</label>
                <select 
                  className="brutal-input" 
                  value={targetGoal} 
                  onChange={(e) => setTargetGoal(e.target.value as any)}
                  style={{ width: "100%" }}
                >
                  <option value="hobby">Personal</option>
                  <option value="professional">Career</option>
                  <option value="exam">Exam</option>
                </select>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
              <div className="dashboard-value-row">
                <label className="section-title">Hours / Week</label>
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
                <label className="section-title">Tools Ready?</label>
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

            {skillQuestions.length > 0 && (
              <div className="brutal-card" style={{ marginBottom: "16px", padding: "14px" }}>
                <DynamicQuestionForm 
                  questions={skillQuestions}
                  answers={dynamicAnswers}
                  onAnswerChange={(id, val) => setDynamicAnswers(prev => ({ ...prev, [id]: val }))}
                />
              </div>
            )}

            {composeError && (
              <div className="brutal-card brutal-card--red" style={{ padding: "10px", fontSize: "12px", marginBottom: "12px" }}>
                <strong>FORM ERROR:</strong> {composeError}
              </div>
            )}

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

            <div className="brutal-card brutal-card--muted" style={{ padding: "12px", marginBottom: "8px" }}>
              <p className="section-title" style={{ marginBottom: "8px" }}>Roadmap Generation</p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "12px" }}>
                <div><strong>Input Skill:</strong> {selectedSkill?.name || currentSkill.skillName || "Not selected"}</div>
                <div><strong>Target Goal:</strong> {targetGoal}</div>
                <div><strong>Intensity:</strong> {hoursPerWeek} hrs/week</div>
                <div><strong>Resources:</strong> {hasTools ? "ready" : "not ready"}</div>
              </div>
              <p style={{ margin: "10px 0 0 0", fontSize: "11px" }}>
                The roadmap engine merges discovered skill structure, your profile context, and your form answers into a deterministic phase plan.
              </p>
            </div>

            <BrutalButton
              variant="primary"
              onClick={onGenerateRoadmap}
              disabled={generating}
              style={{ width: "100%", marginTop: "10px", padding: "16px" }}
            >
              {generating ? "BUILDING ROADMAP..." : "CREATE ROADMAP"}
            </BrutalButton>
          </div>
        </div>
      )}
    </main>
  );
}
