import { useNavigate } from "react-router-dom";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { useNavigationStore } from "../store/navigationStore";

export function RoadmapView() {
  const navigate = useNavigate();
  const { currentSkill, roadmapState } = useNavigationStore();
  if (!roadmapState.isGenerated) return <main style={{ padding: "2rem" }}><p>Roadmap is locked. Generate roadmap from Skills first.</p></main>;

  return (
    <main className="roadmap-page">
      <div className="roadmap-header">
        <h1 className="headline">{currentSkill.skillName || "Skill"}</h1>
      </div>
      <div className="roadmap-timeline">
        {roadmapState.phases.map((phase) => (
          <BrutalCard key={phase.id} className={phase.status === "locked" ? "brutal-card--muted" : ""}>
            <h2>{phase.name}</h2>
            <p className="small-copy">Status: {phase.status}</p>
            {phase.status !== "locked" ? (
              <>
                {phase.competencies.map((competency) => (
                  <div key={competency.name} style={{ marginTop: "0.75rem" }}>
                    <h3>{competency.name}</h3>
                    {competency.techniques.map((technique) => (
                      <div key={technique.id} className="confirm-box">
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <strong>{technique.name}</strong>
                          {technique.status === "active" ? (
                            <BrutalButton variant="primary" onClick={() => navigate(`/session?phase=${phase.id}&technique=${technique.id}`)}>
                              Start Session
                            </BrutalButton>
                          ) : null}
                        </div>
                        {technique.checkpoints.map((checkpoint) => (
                          <div className="checkpoint-row" key={checkpoint.id}>
                            <div>
                              <p>{checkpoint.description}</p>
                              <p className="small-copy">Pass threshold: {checkpoint.threshold}</p>
                              {checkpoint.validationReason ? <p className="small-copy">Failure reason: {checkpoint.validationReason}</p> : null}
                            </div>
                            <div>
                              <span className={`status-pill status-pill--${checkpoint.status === "passed" ? "passed" : checkpoint.status === "failed" ? "failed" : checkpoint.status === "attempted" ? "attempted" : "pending"}`}>
                                {checkpoint.status}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                ))}
              </>
            ) : (
              <p className="small-copy">Locked until previous phase is complete.</p>
            )}
          </BrutalCard>
        ))}
      </div>
    </main>
  );
}
