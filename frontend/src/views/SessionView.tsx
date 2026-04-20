import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { MetricBar } from "../components/brutal/MetricBar";
import { useSubmitSessionMetrics } from "../hooks/useSession";

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
  const [metricCount, setMetricCount] = useState(0);
  const submitMetrics = useSubmitSessionMetrics();

  const nextStep = useMemo(() => {
    return protocolSteps.find((step) => !completedSteps.includes(step.id));
  }, [completedSteps]);

  function markStepComplete(stepId: string) {
    if (completedSteps.includes(stepId)) {
      return;
    }

    setCompletedSteps((previous) => [...previous, stepId]);
    setMetricCount((value) => value + 1);

    submitMetrics.mutate({
      session_id: sessionId,
      accuracy: 0.9,
      elapsed_seconds: 30 + metricCount * 10,
      errors: 0,
      retry: 0,
    });
  }

  return (
    <main className="session-page">
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
                <BrutalButton
                  data-testid={`step-${step.id}-complete`}
                  onClick={() => markStepComplete(step.id)}
                  disabled={!isCurrent}
                >
                  Mark Complete
                </BrutalButton>
              </div>
            );
          })}
        </BrutalCard>

        <BrutalCard className="metrics-panel">
          <h2 className="section-title">Metrics</h2>
          <MetricBar label="Accuracy" value={Math.min(1, 0.65 + metricCount * 0.08)} />
          <MetricBar label="Time" value={Math.min(1, 0.2 + metricCount * 0.12)} />
          <MetricBar label="Errors" value={Math.max(0, 0.5 - metricCount * 0.1)} />
          <MetricBar label="Retry" value={0} />
          <p data-testid="metrics-sent">Metrics sent: {metricCount}</p>

          <div className="button-row">
            <BrutalButton onClick={() => navigate("/roadmap/drawing")}>View Roadmap</BrutalButton>
          </div>
        </BrutalCard>
      </section>
    </main>
  );
}
