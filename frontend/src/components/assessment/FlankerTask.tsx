import React, { useCallback, useEffect, useRef, useState } from "react";

import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export interface FlankerTaskProps {
  onComplete: (results: Record<string, unknown>) => void;
  onRunStateChange?: (running: boolean) => void;
  sessionLevel?: number;
}

interface TrialDef {
  type: "congruent" | "incongruent";
  direction: "left" | "right";
  stimulus: string;
}

interface TrialRecord extends TrialDef {
  response: "left" | "right" | null;
  correct: boolean;
  responseTime: number | null;
}

function buildTrials(totalTrials: number, congruentRatio: number): TrialDef[] {
  const trials: TrialDef[] = [];
  const congruentCount = Math.floor(totalTrials * congruentRatio);
  const incongruentCount = totalTrials - congruentCount;

  for (let i = 0; i < congruentCount; i++) {
    const direction = Math.random() < 0.5 ? "left" : "right";
    trials.push({
      type: "congruent",
      direction,
      stimulus: direction === "left" ? "← ← ← ← ←" : "→ → → → →",
    });
  }
  for (let i = 0; i < incongruentCount; i++) {
    const direction = Math.random() < 0.5 ? "left" : "right";
    const flank = direction === "left" ? "→" : "←";
    const center = direction === "left" ? "←" : "→";
    trials.push({
      type: "incongruent",
      direction,
      stimulus: `${flank} ${flank} ${center} ${flank} ${flank}`,
    });
  }
  for (let i = trials.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [trials[i], trials[j]] = [trials[j], trials[i]];
  }
  return trials;
}

export const FlankerTask: React.FC<FlankerTaskProps> = ({
  onComplete,
  onRunStateChange,
  sessionLevel = 1,
}) => {
  const totalTrials = 60;
  const congruentRatio = 0.5;
  const stimulusDuration = 2000;
  const isi = 1000;
  const fixationDuration = 500;

  const [phase, setPhase] = useState<"intro" | "running" | "done">("intro");
  const [trialIndexDisplay, setTrialIndexDisplay] = useState(1);
  const [stimulusText, setStimulusText] = useState("+");
  const [buttonsEnabled, setButtonsEnabled] = useState(false);
  const [feedback, setFeedback] = useState<"correct" | "wrong" | null>(null);

  const defsRef = useRef<TrialDef[]>([]);
  const recordsRef = useRef<TrialRecord[]>([]);
  const indexRef = useRef(0);
  const waitingRef = useRef(false);
  const startTsRef = useRef(0);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const responseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
    if (responseTimerRef.current) {
      clearTimeout(responseTimerRef.current);
      responseTimerRef.current = null;
    }
  }, []);

  const schedule = useCallback((fn: () => void, ms: number) => {
    const id = setTimeout(() => {
      timersRef.current = timersRef.current.filter((t) => t !== id);
      fn();
    }, ms);
    timersRef.current.push(id);
  }, []);

  const computeMetrics = useCallback(() => {
    const records = recordsRef.current;
    const congRt: number[] = [];
    const incongRt: number[] = [];
    let congCorrect = 0;
    let congTotal = 0;
    let incongCorrect = 0;
    let incongTotal = 0;

    for (const r of records) {
      if (r.type === "congruent") {
        congTotal++;
        if (r.correct) {
          congCorrect++;
          if (r.responseTime != null) congRt.push(r.responseTime);
        }
      } else {
        incongTotal++;
        if (r.correct) {
          incongCorrect++;
          if (r.responseTime != null) incongRt.push(r.responseTime);
        }
      }
    }

    const totalCorrect = congCorrect + incongCorrect;
    const totalResponses = records.length;
    const accuracy = totalResponses > 0 ? totalCorrect / totalResponses : 0;
    const allRT = [...congRt, ...incongRt];
    const meanResponseTime = allRT.length > 0 ? allRT.reduce((a, b) => a + b, 0) / allRT.length : 0;
    let responseTimeVariance = 0;
    if (congRt.length > 0 && incongRt.length > 0) {
      const ca = congRt.reduce((a, b) => a + b, 0) / congRt.length;
      const ia = incongRt.reduce((a, b) => a + b, 0) / incongRt.length;
      responseTimeVariance = ia - ca;
    }
    const halfway = Math.floor(allRT.length / 2);
    const firstHalf = allRT.slice(0, halfway);
    const secondHalf = allRT.slice(halfway);
    const fa = firstHalf.length ? firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length : 0;
    const sa = secondHalf.length ? secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length : 0;
    const performanceDecay = fa > 0 ? (sa - fa) / fa : 0;
    const errorTrials = records.filter((t, i) => i > 0 && !records[i - 1].correct && t.correct);
    const totalErrors = records.filter((t) => !t.correct).length;
    const recoverySlope = totalErrors > 0 ? errorTrials.length / totalErrors : 0;

    return {
      accuracy,
      mean_response_time: meanResponseTime,
      response_time_variance: responseTimeVariance,
      performance_decay: performanceDecay,
      retry_depth: 1 - accuracy,
      dropout_depth_index: 1 - accuracy,
      recovery_slope: recoverySlope,
      raw: {
        total_trials: totalTrials,
        congruent_trials: congTotal,
        incongruent_trials: incongTotal,
        congruent_correct: congCorrect,
        incongruent_correct: incongCorrect,
        congruent_reaction_times: congRt,
        incongruent_reaction_times: incongRt,
        congruent_avg_rt: congRt.length ? congRt.reduce((a, b) => a + b, 0) / congRt.length : 0,
        incongruent_avg_rt: incongRt.length ? incongRt.reduce((a, b) => a + b, 0) / incongRt.length : 0,
        flanker_interference_cost: responseTimeVariance,
        trial_data: records,
        session_level: sessionLevel,
      },
    };
  }, [sessionLevel]);

  const finish = useCallback(() => {
    clearTimers();
    waitingRef.current = false;
    setButtonsEnabled(false);
    setPhase("done");
    onRunStateChange?.(false);
    onComplete(computeMetrics());
  }, [clearTimers, computeMetrics, onComplete, onRunStateChange]);

  const runNextTrial = useCallback(() => {
    if (indexRef.current >= totalTrials) {
      finish();
      return;
    }

    const def = defsRef.current[indexRef.current];
    setTrialIndexDisplay(indexRef.current + 1);
    setStimulusText("+");
    setFeedback(null);
    setButtonsEnabled(false);

    schedule(() => {
      setStimulusText(def.stimulus);
      startTsRef.current = performance.now();
      waitingRef.current = true;
      setButtonsEnabled(true);

      responseTimerRef.current = setTimeout(() => {
        if (!waitingRef.current) return;
        waitingRef.current = false;
        setButtonsEnabled(false);
        recordsRef.current.push({
          ...def,
          response: null,
          correct: false,
          responseTime: null,
        });
        setStimulusText("+");
        indexRef.current += 1;
        schedule(() => runNextTrial(), isi);
      }, stimulusDuration);
    }, fixationDuration);
  }, [finish, fixationDuration, isi, schedule, stimulusDuration, totalTrials]);

  const handleResponse = useCallback(
    (direction: "left" | "right") => {
      if (!waitingRef.current) return;
      if (responseTimerRef.current) {
        clearTimeout(responseTimerRef.current);
        responseTimerRef.current = null;
      }
      waitingRef.current = false;
      setButtonsEnabled(false);

      const def = defsRef.current[indexRef.current];
      const rt = performance.now() - startTsRef.current;
      const correct = direction === def.direction;
      recordsRef.current.push({
        ...def,
        response: direction,
        correct,
        responseTime: rt,
      });
      setFeedback(correct ? "correct" : "wrong");
      setStimulusText("+");
      indexRef.current += 1;
      schedule(() => runNextTrial(), isi + 400);
    },
    [isi, runNextTrial, schedule]
  );

  const startTest = () => {
    defsRef.current = buildTrials(totalTrials, congruentRatio);
    recordsRef.current = [];
    indexRef.current = 0;
    setTrialIndexDisplay(1);
    setPhase("running");
    onRunStateChange?.(true);
    runNextTrial();
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (phase !== "running" || !waitingRef.current) return;
      if (e.code === "ArrowLeft") {
        e.preventDefault();
        handleResponse("left");
      } else if (e.code === "ArrowRight") {
        e.preventDefault();
        handleResponse("right");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [phase, handleResponse]);

  useEffect(
    () => () => {
      clearTimers();
    },
    [clearTimers]
  );

  if (phase === "intro") {
    return (
      <BrutalCard accent="muted" className="assessment-task-intro">
        <h3 className="headline">Flanker task</h3>
        <p>Focus on the center arrow. Ignore flankers.</p>
        <p>Use ← → keys or the on-screen buttons.</p>
        <p className="small-copy">{totalTrials} trials — about 3–4 minutes.</p>
        <BrutalButton variant="primary" onClick={startTest} data-testid="task-start">
          Start test
        </BrutalButton>
      </BrutalCard>
    );
  }

  if (phase === "done") {
    return (
      <BrutalCard accent="green" className="assessment-task-intro">
        <h3 className="headline">Level complete</h3>
        <p className="small-copy">Results are saved for this session.</p>
      </BrutalCard>
    );
  }

  const progress = (trialIndexDisplay / totalTrials) * 100;
  const records = recordsRef.current;
  const congRt = records.filter((r) => r.type === "congruent" && r.correct && r.responseTime != null);
  const incongRt = records.filter((r) => r.type === "incongruent" && r.correct && r.responseTime != null);
  const congAvg =
    congRt.length > 0
      ? Math.round(congRt.reduce((s, r) => s + (r.responseTime as number), 0) / congRt.length)
      : 0;
  const incongAvg =
    incongRt.length > 0
      ? Math.round(incongRt.reduce((s, r) => s + (r.responseTime as number), 0) / incongRt.length)
      : 0;
  const interference = congRt.length && incongRt.length ? incongAvg - congAvg : 0;
  const correctN = records.filter((r) => r.correct).length;
  const errorsN = records.length - correctN;

  const color =
    feedback === "wrong" ? "#c62828" : feedback === "correct" ? "#2e7d32" : "var(--accent-green, #2e7d32)";

  return (
    <BrutalCard accent="white" className="assessment-flanker">
      <div
        style={{
          height: 10,
          borderRadius: 6,
          background: "rgba(0,0,0,0.08)",
          overflow: "hidden",
          marginBottom: 12,
        }}
      >
        <div style={{ width: `${progress}%`, height: "100%", background: "linear-gradient(90deg,#2196F3,#4CAF50)" }} />
      </div>
      <p style={{ textAlign: "center", fontSize: 13, marginBottom: 8 }}>
        Trial {trialIndexDisplay} / {totalTrials}
      </p>
      <div
        style={{
          minHeight: 120,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
          margin: "16px 0",
        }}
      >
        <span style={{ fontSize: "3rem", fontWeight: 700, letterSpacing: 4, color }}>{stimulusText}</span>
        {feedback && (
          <span
            style={{
              position: "absolute",
              fontSize: "2rem",
              fontWeight: 800,
              color: feedback === "correct" ? "#2e7d32" : "#c62828",
            }}
          >
            {feedback === "correct" ? "✓" : "✗"}
          </span>
        )}
      </div>
      <div style={{ display: "flex", justifyContent: "center", gap: 24, marginBottom: 16 }}>
        <BrutalButton type="button" disabled={!buttonsEnabled} onClick={() => handleResponse("left")}>
          ←
        </BrutalButton>
        <BrutalButton type="button" disabled={!buttonsEnabled} onClick={() => handleResponse("right")}>
          →
        </BrutalButton>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6, fontSize: 12 }}>
        <span>Correct: {correctN}</span>
        <span>Errors: {errorsN}</span>
        <span>Congruent RT: {congAvg} ms</span>
        <span>Incongruent RT: {incongAvg} ms</span>
        <span>Interference: {interference} ms</span>
      </div>
    </BrutalCard>
  );
};
