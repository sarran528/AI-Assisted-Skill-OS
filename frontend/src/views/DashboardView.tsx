import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { StatBlock } from "../components/brutal/StatBlock";
import { useGenerateRoadmap } from "../hooks/useRoadmap";
import { useStartSession } from "../hooks/useSession";
import { useSkills, useSubmitGrounding } from "../hooks/useSkills";
import type { SkillItem } from "../types";

const defaultSkills: SkillItem[] = [
  { skill_id: "drawing", name: "Drawing", domain: "arts" },
  { skill_id: "python_basics", name: "Python Basics", domain: "coding" },
];

export function DashboardView() {
  const navigate = useNavigate();
  const [selectedSkill, setSelectedSkill] = useState<string>("drawing");
  const [groundingDone, setGroundingDone] = useState(false);
  const [roadmapFingerprint, setRoadmapFingerprint] = useState<string | null>(null);

  const skillsQuery = useSkills();
  const groundingMutation = useSubmitGrounding();
  const generateRoadmapMutation = useGenerateRoadmap();
  const startSessionMutation = useStartSession();

  const skills = useMemo(() => {
    if (skillsQuery.data && skillsQuery.data.length > 0) {
      return skillsQuery.data;
    }
    return defaultSkills;
  }, [skillsQuery.data]);

  function handleGroundingSubmit() {
    groundingMutation.mutate(
      {
        skill_id: selectedSkill,
        recognition: { items: [true, false, true] },
        familiarity: { answers: [0, 1, 0] },
        confidence: { level: 3 },
      },
      {
        onSuccess: () => {
          setGroundingDone(true);
        },
      }
    );
  }

  function handleGenerateRoadmap() {
    generateRoadmapMutation.mutate(selectedSkill, {
      onSuccess: (data) => {
        const fingerprint = data.fingerprint ?? `fp-${selectedSkill}-v1`;
        setRoadmapFingerprint(fingerprint);
        localStorage.setItem("skillos-roadmap-fingerprint", fingerprint);
      },
    });
  }

  function handleEnterSession() {
    startSessionMutation.mutate(
      {
        skill_id: selectedSkill,
        phase: "phase-1",
        technique_id: "technique-1",
      },
      {
        onSuccess: (data) => {
          navigate(`/session/${data.session_id}`);
        },
      }
    );
  }

  return (
    <main className="page-grid">
      <aside className="sidebar">
        <h2 className="sidebar__title">SkillOS</h2>
        <button className="nav-item nav-item--active" type="button">
          Home
        </button>
        <button className="nav-item" type="button">
          My Skills
        </button>
        <button className="nav-item" type="button" onClick={() => navigate("/assessment")}>
          Assessment
        </button>
      </aside>

      <section className="main-panel">
        <BrutalCard accent="yellow" className="roadmap-card">
          <div className="mono-caps">Active Skill</div>
          <h1 className="headline">{selectedSkill.toUpperCase()}</h1>
          <p>Phase 2 of 4 - Intermediate session prep</p>
          <div className="button-row">
            <BrutalButton data-testid="start-assessment" onClick={() => navigate("/assessment")} variant="primary">
              Start Assessment
            </BrutalButton>
            <BrutalButton onClick={handleEnterSession} data-testid="enter-session" disabled={!roadmapFingerprint}>
              Enter Session
            </BrutalButton>
          </div>
        </BrutalCard>

        <BrutalCard className="skill-list-card">
          <h2 className="section-title">Select Skill</h2>
          <div className="skill-grid">
            {skills.map((skill) => (
              <button
                key={skill.skill_id}
                type="button"
                data-testid={`skill-${skill.skill_id}`}
                className={`skill-item ${selectedSkill === skill.skill_id ? "skill-item--active" : ""}`}
                onClick={() => setSelectedSkill(skill.skill_id)}
              >
                <span className="mono-caps">{skill.domain ?? "general"}</span>
                <strong>{skill.name}</strong>
              </button>
            ))}
          </div>

          <div className="grounding-box">
            <p className="mono-caps">Grounding Probes</p>
            <label className="checkbox-row" htmlFor="recognition-0">
              <input id="recognition-0" data-testid="grounding-recognition-0" type="checkbox" defaultChecked />
              Recognition sample 1
            </label>
            <BrutalButton data-testid="grounding-submit" variant="primary" onClick={handleGroundingSubmit}>
              Submit Grounding
            </BrutalButton>
          </div>

          <div className="button-row">
            <BrutalButton
              data-testid="generate-roadmap"
              onClick={handleGenerateRoadmap}
              variant="secondary"
              disabled={!groundingDone}
            >
              Generate Roadmap
            </BrutalButton>
          </div>

          {roadmapFingerprint && (
            <div data-testid="roadmap-fingerprint" className="fingerprint-badge">
              Integrity verified ✓
            </div>
          )}
        </BrutalCard>
      </section>

      <section className="right-panel">
        <h3 className="section-title">Profile Summary</h3>
        <div className="stats-grid">
          <StatBlock value="0.84" label="cognitive cap." accent />
          <StatBlock value="0.71" label="attn stability" />
          <StatBlock value="0.65" label="learn tolerance" />
          <StatBlock value="0.78" label="stress resilience" />
        </div>
      </section>
    </main>
  );
}
