import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { MetricBar } from "../components/brutal/MetricBar";
import { SupportPanel } from "../components/brutal/SupportPanel";
import {
  useCompleteSession,
  useSubmitSessionMetrics,
  useUploadEvidence,
  useValidateCheckpoint,
} from "../hooks/useSession";

const protocolSteps = [
  { id: "1", title: "Set up materials" },
  { id: "2", title: "Execute technique" },
  { id: "3", title: "Review output" },
  { id: "4", title: "Record observations" },
];

export function SessionView() {
  const { sessionId = "session-local" } = useParams();
  const navigate = useNavigate();

  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [metricsSentCount, setMetricsSentCount] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<"idle" | "uploaded" | "failed">("idle");
  const [showConfirm, setShowConfirm] = useState(false);
  const [completionMessage, setCompletionMessage] = useState<string>("");
  const [protocolWarning, setProtocolWarning] = useState<string>("");
  const [isDragOver, setIsDragOver] = useState(false);
  const [supportOpen, setSupportOpen] = useState(false);
  const [tipPending, setTipPending] = useState(false);

  const submitMetrics = useSubmitSessionMetrics();
  const uploadEvidence = useUploadEvidence();
  const completeSession = useCompleteSession();
  const validateCheckpoint = useValidateCheckpoint();

  const nextStep = useMemo(() => {
    return protocolSteps.find((step) => !completedSteps.includes(step.id));
  }, [completedSteps]);

  const progressRatio = completedSteps.length / protocolSteps.length;
  const currentAccuracy = Math.min(0.95, 0.58 + completedSteps.length * 0.09);
  const currentTimeEfficiency = Math.min(1, 0.2 + completedSteps.length * 0.18);
  const currentErrors = Math.max(0, 0.6 - completedSteps.length * 0.12);

  function sendMetrics(progressCount: number) {
    submitMetrics.mutate({
      session_id: sessionId,
      accuracy: Math.min(0.95, 0.58 + progressCount * 0.09),
      elapsed_seconds: 35 + progressCount * 20,
      errors: Math.max(0, 3 - progressCount),
      retry: progressCount > 2 ? 1 : 0,
    });
    setMetricsSentCount((value) => value + 1);
  }

  useEffect(() => {
    if (completedSteps.length === 0) {
      return;
    }

    const interval = window.setInterval(() => {
      sendMetrics(completedSteps.length);
    }, 10_000);

    return () => window.clearInterval(interval);
    // Intentionally bind this to step count so fresh values are used each interval cycle.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [completedSteps.length, sessionId]);

  function markStepComplete(stepId: string) {
    if (completedSteps.includes(stepId)) {
      return;
    }

    if (nextStep?.id !== stepId) {
      setProtocolWarning(`Follow protocol order. Complete step ${nextStep?.id ?? "N/A"} first.`);
      return;
    }

    setProtocolWarning("");
    const nextCompletedCount = completedSteps.length + 1;
    setCompletedSteps((previous) => [...previous, stepId]);
    sendMetrics(nextCompletedCount);
  }

  function handleUploadEvidence() {
    if (!selectedFile) {
      return;
    }

    uploadEvidence.mutate(
      {
        sessionId: sessionId,
        checkpointId: "checkpoint-1",
        file: selectedFile,
      },
      {
        onSuccess: () => setUploadState("uploaded"),
        onError: () => setUploadState("failed"),
      }
    );
  }

  function onDropFile(file: File | null) {
    setIsDragOver(false);
    if (!file) {
      return;
    }
    setSelectedFile(file);
    setUploadState("idle");
  }

  function handleConfirmComplete() {
    if (completedSteps.length < protocolSteps.length) {
      setCompletionMessage("Complete all protocol steps before finishing the session.");
      setShowConfirm(false);
      return;
    }

    completeSession.mutate(
      {
        session_id: sessionId,
        completed_steps: completedSteps,
      },
      {
        onSuccess: async (response) => {
          setShowConfirm(false);
          const requiresTip = Boolean(response.tip_pending && !response.passed);
          setTipPending(requiresTip);
          if (requiresTip) {
            setSupportOpen(true);
          }

          try {
            const validation = await validateCheckpoint.mutateAsync({
              sessionId: sessionId,
              checkpointId: "checkpoint-1",
            });

            if (response.passed && validation.passed) {
              setCompletionMessage("Session complete and checkpoint passed.");
            } else if (!response.passed) {
              setCompletionMessage(
                response.failure_reason
                  ? `Session failed: ${response.failure_reason}. Review corrective tip in Support Panel.`
                  : "Session failed. Review corrective tip in Support Panel."
              );
            } else {
              setCompletionMessage("Session complete but checkpoint failed.");
            }
          } catch {
            setCompletionMessage("Session complete. Validation pending.");
          }
        },
      }
    );
  }

  return (
    <main className="session-page" data-testid="session-screen">
      <header className="top-bar">
        <strong>Blind Contour Drawing</strong>
        <span data-testid="session-id" data-session-id={sessionId}>
          Session #{sessionId.slice(0, 8)}
        </span>
        <span className="live-indicator">LIVE ●</span>
      </header>

      <section className="session-grid">
        <BrutalCard className="protocol-panel">
          <h2 className="section-title">Protocol</h2>
          {protocolSteps.map((step) => {
            const completed = completedSteps.includes(step.id);
            const isCurrent = nextStep?.id === step.id;
            return (
              <div
                key={step.id}
                className={`protocol-row ${completed ? "protocol-row--done" : ""} ${isCurrent ? "protocol-row--active" : ""}`}
              >
                <span>{completed ? "✓" : isCurrent ? "●" : "○"}</span>
                <span>{step.title}</span>
                <BrutalButton data-testid={`step-${step.id}-complete`} onClick={() => markStepComplete(step.id)}>
                  Mark Complete
                </BrutalButton>
              </div>
            );
          })}

          {protocolWarning ? <p className="error-text" data-testid="protocol-warning">{protocolWarning}</p> : null}

          <MetricBar label="Step Progress" value={progressRatio} />
        </BrutalCard>

        <BrutalCard className="metrics-panel">
          <h2 className="section-title">Metrics</h2>
          <MetricBar label="Accuracy" value={currentAccuracy} />
          <MetricBar label="Time" value={currentTimeEfficiency} />
          <MetricBar label="Errors" value={currentErrors} />
          <MetricBar label="Retry" value={tipPending ? 0.45 : 0.1} />
          <p data-testid="metrics-sent">Metrics sent: {metricsSentCount}</p>

          <div
            className={`evidence-drop-zone ${isDragOver ? "evidence-drop-zone--active" : ""}`}
            data-testid="evidence-drop-zone"
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={(event) => {
              event.preventDefault();
              const file = event.dataTransfer.files?.[0] ?? null;
              onDropFile(file);
            }}
          >
            <p>Drag evidence here or use file picker</p>
            <input
              data-testid="evidence-upload"
              type="file"
              onChange={(event) => onDropFile(event.target.files?.[0] ?? null)}
            />
            {selectedFile ? <p className="small-copy">Selected: {selectedFile.name}</p> : null}
            <BrutalButton data-testid="upload-evidence-btn" onClick={handleUploadEvidence} disabled={!selectedFile}>
              Upload Evidence
            </BrutalButton>
            {uploadState === "uploaded" && <p data-testid="evidence-uploaded">Evidence uploaded</p>}
            {uploadState === "failed" && <p className="error-text">Evidence upload failed</p>}
          </div>

          <div className="button-row">
            <BrutalButton data-testid="complete-session" variant="primary" onClick={() => setShowConfirm(true)}>
              Complete Session
            </BrutalButton>
            <BrutalButton data-testid="open-support-panel" onClick={() => setSupportOpen(true)}>
              Open Support
            </BrutalButton>
          </div>

          {showConfirm ? (
            <div className="confirm-box">
              <p>Confirm completion?</p>
              <p className="small-copy">Completed steps: {completedSteps.length} / {protocolSteps.length}</p>
              <BrutalButton data-testid="confirm-complete" onClick={handleConfirmComplete}>
                Confirm
              </BrutalButton>
            </div>
          ) : null}

          {completionMessage ? <p data-testid="completion-message">{completionMessage}</p> : null}

          <div className="button-row">
            <BrutalButton onClick={() => navigate("/roadmap/drawing")} data-testid="view-roadmap-from-session">
              View Roadmap
            </BrutalButton>
          </div>
        </BrutalCard>
      </section>

      <SupportPanel
        open={supportOpen}
        onClose={() => setSupportOpen(false)}
        skillId={localStorage.getItem("skillos-active-skill") ?? "drawing"}
        phase="phase-1"
        techniqueId="technique-1"
        sessionId={sessionId}
        tipPending={tipPending}
      />
    </main>
  );
}
