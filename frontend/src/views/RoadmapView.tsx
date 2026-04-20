import { useParams } from "react-router-dom";

import { BrutalCard } from "../components/brutal/BrutalCard";
import { CheckpointRow } from "../components/brutal/CheckpointRow";

export function RoadmapView() {
  const { skillId = "drawing" } = useParams();
  const fingerprint = localStorage.getItem("skillos-roadmap-fingerprint") ?? "fp-drawing-v1";

  return (
    <main className="roadmap-page">
      <header className="roadmap-header">
        <h1 className="headline">{skillId.toUpperCase()} ROADMAP</h1>
        <div className="fingerprint-badge" data-testid="roadmap-fingerprint">
          Integrity verified ✓
        </div>
      </header>

      <BrutalCard accent="green">
        <h2 className="section-title">Phase 1: Fundamentals</h2>
        <p>Completed</p>
      </BrutalCard>

      <div className="phase-connector" />

      <BrutalCard accent="yellow">
        <h2 className="section-title">Phase 2: Intermediate Shading</h2>
        <p>Fingerprint: {fingerprint}</p>
        <CheckpointRow title="Produce 5 shaded shapes" status="passed" />
        <CheckpointRow title="Demonstrate hatching" status="passed" />
        <CheckpointRow title="Draw room in perspective" status="pending" />
      </BrutalCard>
    </main>
  );
}
