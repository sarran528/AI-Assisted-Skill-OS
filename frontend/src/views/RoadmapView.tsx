import { useState } from "react";
import { useParams } from "react-router-dom";

import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { CheckpointRow } from "../components/brutal/CheckpointRow";
import { SupportPanel } from "../components/brutal/SupportPanel";

const phaseTimeline = [
  {
    id: "phase-1",
    title: "Phase 1: Fundamentals",
    status: "completed",
    estimate: "Weeks 1-2",
  },
  {
    id: "phase-2",
    title: "Phase 2: Intermediate Shading",
    status: "active",
    estimate: "Weeks 3-5",
  },
  {
    id: "phase-3",
    title: "Phase 3: Composition",
    status: "locked",
    estimate: "Weeks 6-8",
  },
];

export function RoadmapView() {
  const { skillId = "drawing" } = useParams();
  const fingerprint = localStorage.getItem("skillos-roadmap-fingerprint") ?? "fp-drawing-v1";
  const [showParameters, setShowParameters] = useState(false);
  const [supportOpen, setSupportOpen] = useState(false);

  return (
    <main className="roadmap-page" data-testid="roadmap-screen">
      <header className="roadmap-header">
        <h1 className="headline">{skillId.toUpperCase()} ROADMAP</h1>
        <div className="fingerprint-badge" data-testid="roadmap-fingerprint">
          Integrity verified ✓
        </div>
      </header>

      <BrutalCard className="roadmap-params" accent="blue">
        <div className="roadmap-params__header">
          <h2 className="section-title">Roadmap Parameters</h2>
          <BrutalButton
            data-testid="toggle-params"
            onClick={() => setShowParameters((value) => !value)}
            variant="secondary"
          >
            {showParameters ? "Hide" : "Show"} Parameters
          </BrutalButton>
        </div>
        {showParameters ? (
          <div className="roadmap-params__content" data-testid="params-panel">
            <p>Skill: {skillId}</p>
            <p>Current Phase: phase-2</p>
            <p>Cadence: 4 sessions / week</p>
            <p>Session Duration: 45 minutes</p>
            <p>Integrity Fingerprint: {fingerprint}</p>
          </div>
        ) : null}
      </BrutalCard>

      <section className="roadmap-timeline" data-testid="roadmap-timeline">
        {phaseTimeline.map((phase, index) => {
          const accent = phase.status === "completed" ? "green" : phase.status === "active" ? "yellow" : "muted";

          return (
            <div className="roadmap-timeline-item" key={phase.id}>
              <BrutalCard accent={accent}>
                <h2 className="section-title">{phase.title}</h2>
                <p>{phase.estimate}</p>
                <p className="mono-caps">{phase.status.toUpperCase()}</p>
                {phase.id === "phase-2" ? (
                  <>
                    <CheckpointRow title="Produce 5 shaded shapes" status="passed" />
                    <CheckpointRow title="Demonstrate hatching" status="passed" />
                    <CheckpointRow title="Draw room in perspective" status="pending" />
                  </>
                ) : null}
              </BrutalCard>
              {index < phaseTimeline.length - 1 ? <div className="phase-connector" /> : null}
            </div>
          );
        })}
      </section>

      <BrutalButton data-testid="open-support-panel" className="support-fab" onClick={() => setSupportOpen(true)}>
        Support
      </BrutalButton>

      <SupportPanel
        open={supportOpen}
        onClose={() => setSupportOpen(false)}
        skillId={skillId}
        phase="phase-2"
        techniqueId="hatching"
      />
    </main>
  );
}
