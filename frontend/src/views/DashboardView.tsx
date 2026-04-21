import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { CreateSkillCard } from "../components/home/CreateSkillCard";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { StatBlock } from "../components/brutal/StatBlock";
import { useRecentSessions, useStartSession } from "../hooks/useSession";
import { useSkills } from "../hooks/useSkills";
import type { SkillItem } from "../types";
import {
  AssistantCard,
  ResourceCard,
  EvidenceHistoryCard,
  LevelProgressCard,
} from "../components";

export function DashboardView() {
  const navigate = useNavigate();
  const [selectedSkill, setSelectedSkill] = useState<string>("");

  const skillsQuery = useSkills();
  const startSessionMutation = useStartSession();

  const recentSessionsQuery = useRecentSessions(6);
  const skills = useMemo(() => skillsQuery.data ?? [], [skillsQuery.data]);

  useEffect(() => {
    if (!selectedSkill && skills.length > 0) {
      setSelectedSkill(skills[0].skill_id);
    }
  }, [selectedSkill, skills]);

  function handleEnterSession() {
    if (!selectedSkill) {
      return;
    }
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

  /**
   * PRE-SKILL STATE: SkillRoadmap == null AND BaselineSkillState == null
   * Indicator: skills.length === 0 AND not loading
   * Render: Only CreateSkillCard, no other UI elements
   */
  const isPreSkillState = !skillsQuery.isLoading && skills.length === 0;

  if (isPreSkillState) {
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

        <section className="main-panel main-panel--centered">
          <CreateSkillCard />
        </section>
      </main>
    );
  }

  /**
   * POST-SKILL STATE: Active progression
   * Render: Full dashboard with skills, assessment, sessions, roadmap
   */
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
        <button className="nav-item" type="button" onClick={() => navigate(`/roadmap/${selectedSkill}`)}>
          Roadmap
        </button>
      </aside>

      <section className="main-panel">
        <BrutalCard className="skill-list-card">
          <h2 className="section-title">Available Skills</h2>
          <div className="skill-grid">
            {skillsQuery.isLoading ? (
              <div className="skill-item skill-item--placeholder">Loading skills...</div>
            ) : skills.length === 0 ? (
              <div className="skill-item skill-item--placeholder">No skills available yet.</div>
            ) : (
              skills.map((skill) => (
                <div
                  key={skill.skill_id}
                  data-testid={`skill-${skill.skill_id}`}
                  className="skill-item"
                >
                  <div className="skill-card__header">
                    <strong>{skill.name}</strong>
                    <span className="mono-caps">Domain: {skill.domain ?? "general"}</span>
                  </div>
                  <div className="skill-card__meta">
                    <span>ID: {skill.skill_id}</span>
                  </div>
                  <div className="skill-card__actions">
                    <BrutalButton
                      data-testid={`start-assessment-${skill.skill_id}`}
                      variant="primary"
                      onClick={() => {
                        setSelectedSkill(skill.skill_id);
                        localStorage.setItem("skillos-active-skill", skill.skill_id);
                        navigate("/assessment");
                      }}
                    >
                      Start Assessment
                    </BrutalButton>
                  </div>
                </div>
              ))
            )}
          </div>
        </BrutalCard>
      </section>

      <section className="right-panel">
        <h3 className="section-title">Profile Summary</h3>
        <div className="stats-grid">
          <StatBlock value="--" label="cognitive cap." accent />
          <StatBlock value="--" label="attn stability" />
          <StatBlock value="--" label="learn tolerance" />
          <StatBlock value="--" label="stress resilience" />
        </div>

        <AssistantCard />
        <ResourceCard />
        <EvidenceHistoryCard />
        <LevelProgressCard />

        <BrutalCard className="dashboard-card" accent="yellow" testId="phase-progress-card">
          <h3>Phase Progress</h3>
          <div className="phase-pips" data-testid="phase-pips">
            <span className="phase-pip phase-pip--done" />
            <span className="phase-pip phase-pip--done" />
            <span className="phase-pip phase-pip--active" />
            <span className="phase-pip" />
            <span className="phase-pip" />
          </div>
          <p>Phase B complete. Phase C unlocked.</p>
          <BrutalButton data-testid="view-roadmap-btn" onClick={() => navigate(`/roadmap/${selectedSkill}`)}>
            View Roadmap
          </brutalbutton>
        </BrutalCard>

        <BrutalCard className="dashboard-card" accent="blue" testId="recent-sessions-card">
          <h3>Recent Sessions</h3>
          <div className="recent-session-list">
            {recentSessionsQuery.isLoading ? (
              <div className="empty-state">Loading sessions...</div>
            ) : recentSessionsQuery.data && recentSessionsQuery.data.length > 0 ? (
              recentSessionsQuery.data.map((session) => (
                <article key={session.session_id} className="recent-session-item">
                  <strong>{session.session_id.slice(0, 8).toUpperCase()}</strong>
                  <span>{session.phase}</span>
                  <span className={`status-pill status-pill--${session.status}`}>{session.status.toUpperCase()}</span>
                  <span>{session.score !== null ? `${Math.round(session.score * 100)}%` : "--"}</span>
                </article>
              ))
            ) : (
              <div className="empty-state">No sessions yet.</div>
            )}
          </div>
          <BrutalButton data-testid="view-sessions-btn" onClick={handleEnterSession}>Open Session</BrutalButton>
        </BrutalCard>
      </section>
    </main>
  );
}
