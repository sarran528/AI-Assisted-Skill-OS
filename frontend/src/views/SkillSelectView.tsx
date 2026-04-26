import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { skillApi } from "../api/skillApi";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { Input } from "../components/ui/Input";
import { useNavigationStore, type RoadmapPhase } from "../store/navigationStore";
import { Skill } from "../components/skill/SkillCard";

export function SkillSelectView() {
  const navigate = useNavigate();
  const { profileState, currentSkill, setCurrentSkill, setRoadmapState, setRoadmapPhases, setSystemState } = useNavigationStore();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [discoverError, setDiscoverError] = useState<string | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [whyLearn, setWhyLearn] = useState("");
  const [experienceLevel, setExperienceLevel] = useState<"beginner" | "intermediate" | "advanced">("beginner");
  const [hasTools, setHasTools] = useState(true);
  const [hoursPerWeek, setHoursPerWeek] = useState(6);
  const [targetGoal, setTargetGoal] = useState<"hobby" | "professional" | "exam">("hobby");
  const [composeError, setComposeError] = useState<string | null>(null);

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

  const onSelectSkill = (skill: Skill) => {
    setSelectedSkill(skill);
    setCurrentSkill({ skillId: skill.skill_id, skillName: skill.name, domain: "General" });
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
      reloadSkills();
      onSelectSkill(discovered);
    } catch (error: any) {
      setDiscoverError(error?.response?.data?.detail ?? "Could not discover skill from internet.");
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
    setSystemState("roadmap_generation");
    setRoadmapState({ isGenerating: true, isGenerated: false });
    skillApi.composeResearch({
      skill_id: activeSkill.skill_id as string,
      why_learn: whyLearn.trim(),
      experience_level: experienceLevel,
      has_required_tools: hasTools,
      hours_per_week: hoursPerWeek,
      target_goal: targetGoal,
    }).then(() => {
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
        <div className="setup-overlay">
          <div className="setup-modal">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
              <div>
                <span className="mono-caps" style={{ color: "var(--color-tertiary)" }}>Skill Initialization</span>
                <h2 className="headline">Configuring {selectedSkill?.name || currentSkill.skillName}</h2>
              </div>
              <button 
                onClick={() => {
                  setSelectedSkill(null);
                  setCurrentSkill({ skillId: null, skillName: null, domain: null });
                }}
                style={{ background: "none", border: "none", cursor: "pointer", fontSize: "24px", fontWeight: "bold" }}
              >
                ×
              </button>
            </div>

            <div className="stepper-header">
              <div className="step-dot active"></div>
              <div className={`step-dot ${whyLearn.length > 5 ? "complete" : ""}`}></div>
              <div className="step-dot"></div>
            </div>

            <div style={{ display: "grid", gap: "20px" }}>
              <div className="dashboard-value-row">
                <label className="section-title">Objective Context</label>
                <textarea
                  className="brutal-input"
                  rows={3}
                  value={whyLearn}
                  onChange={(e) => setWhyLearn(e.target.value)}
                  placeholder="Tell us what you want to achieve with this skill..."
                  style={{ width: "100%", resize: "none" }}
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
        </div>
      )}
    </main>
  );
}
