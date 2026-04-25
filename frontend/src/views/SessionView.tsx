import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { useNavigationStore } from "../store/navigationStore";

export function SessionView() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const phaseId = searchParams.get("phase") || "";
  const techniqueId = searchParams.get("technique") || "";
  const { roadmapState, setSessionState, updateCheckpointStatus, promoteNextPhaseIfNeeded } = useNavigationStore();
  const [step, setStep] = useState(1);
  const [attemptsRemaining, setAttemptsRemaining] = useState(3);
  const [sessionDone, setSessionDone] = useState(false);

  const phase = useMemo(() => roadmapState.phases.find((item) => item.id === phaseId), [phaseId, roadmapState.phases]);
  const technique = useMemo(() => phase?.competencies.flatMap((c) => c.techniques).find((t) => t.id === techniqueId), [phase, techniqueId]);

  if (!phase || !technique) return <main style={{ padding: "2rem" }}><p>No active technique session found.</p></main>;

  return (
    <main style={{ minHeight: "100vh", padding: "2rem" }}>
      <h1 className="headline">{technique.name}</h1>
      <p>Attempts remaining: {attemptsRemaining}</p>
      <p>Session timer running</p>
      <div className="brutal-card">
        {[1, 2, 3].map((protocolStep) => {
          const isDone = step > protocolStep;
          const isActive = step === protocolStep;
          return (
            <div key={protocolStep} className={`protocol-row ${isDone ? "protocol-row--done" : isActive ? "protocol-row--active" : ""}`}>
              <span>{protocolStep}</span>
              <span>Step {protocolStep}</span>
              {!isDone ? (
                <BrutalButton
                  onClick={() => {
                    if (protocolStep === step) setStep((prev) => prev + 1);
                    if (protocolStep === 3) setSessionDone(true);
                    setSessionState({ isActive: true, currentStep: protocolStep, totalSteps: 3 });
                  }}
                >
                  Mark Complete
                </BrutalButton>
              ) : <span>✓</span>}
            </div>
          );
        })}

        {sessionDone ? (
          <div className="evidence-uploader">
            <p>Submit Evidence</p>
            <input className="brutal-input" type="file" />
            <BrutalButton
              variant="primary"
              onClick={() => {
                const targetCheckpoint = technique.checkpoints.find((cp) => cp.status !== "passed");
                if (!targetCheckpoint) return navigate("/roadmap");
                updateCheckpointStatus(phase.id, technique.id, targetCheckpoint.id, "validating");
                navigate("/roadmap");
                window.setTimeout(() => {
                  const passed = Math.random() > 0.35;
                  updateCheckpointStatus(
                    phase.id,
                    technique.id,
                    targetCheckpoint.id,
                    passed ? "passed" : "failed",
                    passed ? undefined : "Accuracy below threshold."
                  );
                  if (!passed) setAttemptsRemaining((prev) => Math.max(0, prev - 1));
                  promoteNextPhaseIfNeeded();
                }, 1000);
              }}
            >
              Submit Evidence
            </BrutalButton>
          </div>
        ) : null}
      </div>
    </main>
  );
}
