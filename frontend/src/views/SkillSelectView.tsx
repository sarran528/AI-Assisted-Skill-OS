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
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [recognition, setRecognition] = useState(3);
  const [familiarity, setFamiliarity] = useState("functions");
  const [confidence, setConfidence] = useState(3);

  useEffect(() => {
    setLoading(true);
    skillApi
      .listSkills()
      .then((res: { data: Skill[] }) => {
        setSkills(res.data);
      })
      .catch(() => setSkills([]))
      .finally(() => setLoading(false));
  }, []);

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

  const onGenerateRoadmap = () => {
    if (!selectedSkill) return;
    setGenerating(true);
    setSystemState("roadmap_generation");
    setRoadmapState({ isGenerating: true, isGenerated: false });
    window.setTimeout(() => {
      const phases = buildRoadmap(selectedSkill.name);
      setRoadmapPhases(phases);
      setRoadmapState({
        isGenerating: false,
        isGenerated: true,
        currentPhase: "Phase 1",
        currentTechnique: "Core Fundamentals",
        roadmapComplete: false,
      });
      setSystemState("roadmap_active");
      setGenerating(false);
      navigate("/roadmap");
    }, 1200);
  };

  if (!profileState.isActive) {
    return <main style={{ padding: "2rem" }}><p>Skills are locked until your profile is active.</p></main>;
  }

  return (
    <main style={{ padding: "2rem" }}>
      <h1 className="headline">Select a skill to learn</h1>
      <div style={{ margin: "1rem 0" }}>
        <Input placeholder="Search skills..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>
      {loading ? <p>Loading skills...</p> : null}
      <div className="skill-grid">
        {filtered.map((skill) => (
          <BrutalCard key={skill.skill_id} className="skill-item">
            <h2>{skill.name}</h2>
            <p className="small-copy">Domain: General</p>
            <p className="small-copy">Brief description: Structured template for {skill.name}.</p>
            <p className="small-copy">Estimated duration: {estimateDuration(skill.complexity)}</p>
            <BrutalButton variant="primary" onClick={() => onSelectSkill(skill)}>Select</BrutalButton>
          </BrutalCard>
        ))}
      </div>
      {selectedSkill || currentSkill.skillId ? (
        <BrutalCard style={{ marginTop: "1rem" }}>
          <h2>Skill grounding probes</h2>
          <p className="small-copy">Recognition: rate familiarity (1-5)</p>
          <input className="brutal-input" type="range" min={1} max={5} value={recognition} onChange={(e) => setRecognition(Number(e.target.value))} />
          <p className="small-copy">Familiarity check: choose core terms</p>
          <select className="brutal-input" value={familiarity} onChange={(e) => setFamiliarity(e.target.value)}>
            <option value="functions">Functions</option>
            <option value="data-structures">Data Structures</option>
            <option value="debugging">Debugging</option>
          </select>
          <p className="small-copy">Confidence estimation (1-5)</p>
          <input className="brutal-input" type="range" min={1} max={5} value={confidence} onChange={(e) => setConfidence(Number(e.target.value))} />
          <BrutalButton variant="primary" onClick={onGenerateRoadmap} disabled={generating}>
            {generating ? "Generating..." : "Generate Roadmap"}
          </BrutalButton>
        </BrutalCard>
      ) : null}
    </main>
  );
}
