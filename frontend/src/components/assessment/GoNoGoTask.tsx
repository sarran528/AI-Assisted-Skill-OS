import React, { useCallback, useEffect, useRef, useState } from "react";

import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export interface GoNoGoTaskProps {
  onComplete: (results: Record<string, unknown>) => void;
  onRunStateChange?: (running: boolean) => void;
  sessionLevel?: number;
}

type TrialType = "go" | "nogo";

interface Trial {
  type: TrialType;
  responded: boolean;
  responseTime: number | null;
  correct: boolean;
}

function normalInverseCDF(p: number): number {
  const a1 = -39.69683028665376;
  const a2 = 220.9460984245205;
  const a3 = -275.9285104469687;
  const a4 = 138.357751867269;
  const a5 = -30.66479806614716;
  const a6 = 2.506628277459239;
  const b1 = -54.47609879822406;
  const b2 = 161.5858368580409;
  const b3 = -155.6989798598866;
  const b4 = 66.80131188771972;
  const b5 = -13.28068155288572;
  const c1 = -0.007784894002430293;
  const c2 = -0.3223964580411365;
  const c3 = -2.400758277161838;
  const c4 = -2.549732539343734;
  const c5 = 4.374664141464968;
  const c6 = 2.938163982698783;
  const d1 = 0.007784695709041462;
  const d2 = 0.3224671290700398;
  const d3 = 2.445134137142996;
  const d4 = 3.754408661907416;
  const pLow = 0.02425;
  const pHigh = 1 - pLow;

  let q: number;
  let r: number;

  if (p < pLow) {
    q = Math.sqrt(-2 * Math.log(p));
    return (
      (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
      ((((d1 * q + d2) * q + d3) * q + d4) * q + 1)
    );
  }

  if (p <= pHigh) {
    q = p - 0.5;
    r = q * q;
    return (
      (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) *
      q /
      (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1)
    );
  }

  q = Math.sqrt(-2 * Math.log(1 - p));
  return (
    -(((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
    ((((d1 * q + d2) * q + d3) * q + d4) * q + 1)
  );
}

function shuffleTrials(trials: Trial[]): void {
  for (let i = trials.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [trials[i], trials[j]] = [trials[j], trials[i]];
  }
}

export const GoNoGoTask: React.FC<GoNoGoTaskProps> = ({
  onComplete,
  onRunStateChange,
  sessionLevel = 1,
}) => {
  const totalTrials = 50;
  const goProbability = 0.6;
  const stimulusDuration = 1000;
  const isi = 1500;

  const [phase, setPhase] = useState<"intro" | "running" | "done">("intro");
  const [displayIndex, setDisplayIndex] = useState(0);
  const [stimulus, setStimulus] = useState<"" | "go" | "nogo">("");
  const [stats, setStats] = useState({
    hits: 0,
    misses: 0,
    falseAlarms: 0,
    correctRejections: 0,
    reactionTimes: [] as number[],
  });

  const trialsRef = useRef<Trial[]>([]);
  const indexRef = useRef(0);
  const waitingRef = useRef(false);
  const stimulusStartRef = useRef(0);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = () => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  };

  const schedule = (fn: () => void, ms: number) => {
    const id = setTimeout(() => {
      timersRef.current = timersRef.current.filter((t) => t !== id);
      fn();
    }, ms);
    timersRef.current.push(id);
  };

  const buildMetricsFromTrials = useCallback(() => {
    const trials = trialsRef.current;
    const totalGoTrials = trials.filter((t) => t.type === "go").length;
    const totalNoGoTrials = trials.filter((t) => t.type === "nogo").length;
    let hits = 0;
    let misses = 0;
    let falseAlarms = 0;
    let correctRejections = 0;
    const reactionTimes: number[] = [];
    for (const t of trials) {
      if (t.type === "go") {
        if (t.responded && t.correct) {
          hits++;
          if (t.responseTime != null) reactionTimes.push(t.responseTime);
        } else if (!t.responded && !t.correct) misses++;
      } else if (t.type === "nogo") {
        if (t.responded && !t.correct) falseAlarms++;
        else if (!t.responded && t.correct) correctRejections++;
      }
    }

    const correctResponses = hits + correctRejections;
    const accuracy = correctResponses / totalTrials;
    const meanResponseTime =
      reactionTimes.length > 0 ? reactionTimes.reduce((a, b) => a + b, 0) / reactionTimes.length : 0;
    const rtVariance =
      reactionTimes.length > 1
        ? reactionTimes.reduce((sum, rt) => sum + (rt - meanResponseTime) ** 2, 0) /
          (reactionTimes.length - 1)
        : 0;
    const halfway = Math.floor(reactionTimes.length / 2);
    const firstHalf = reactionTimes.slice(0, halfway);
    const secondHalf = reactionTimes.slice(halfway);
    const firstHalfAvg = firstHalf.length > 0 ? firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length : 0;
    const secondHalfAvg = secondHalf.length > 0 ? secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length : 0;
    const performanceDecay = firstHalfAvg > 0 ? (secondHalfAvg - firstHalfAvg) / firstHalfAvg : 0;
    const retryDepth = 1 - accuracy;
    const dropoutDepthIndex = misses / totalGoTrials + falseAlarms / Math.max(1, totalNoGoTrials);
    const errorTrials = trials.filter((t, i) => i > 0 && !trials[i - 1].correct && t.correct);
    const recoverySlope = errorTrials.length / Math.max(1, misses + falseAlarms);

    const hitRate = hits / Math.max(1, totalGoTrials);
    const falseAlarmRate = totalNoGoTrials > 0 ? falseAlarms / totalNoGoTrials : 0;
    const adjHit = Math.min(0.99, Math.max(0.01, hitRate));
    const adjFa = Math.min(0.99, Math.max(0.01, falseAlarmRate));
    const dPrime = normalInverseCDF(adjHit) - normalInverseCDF(adjFa);

    return {
      accuracy,
      mean_response_time: meanResponseTime,
      response_time_variance: rtVariance,
      performance_decay: performanceDecay,
      retry_depth: retryDepth,
      dropout_depth_index: dropoutDepthIndex,
      recovery_slope: recoverySlope,
      raw: {
        total_trials: totalTrials,
        go_trials: totalGoTrials,
        nogo_trials: totalNoGoTrials,
        hits,
        misses,
        false_alarms: falseAlarms,
        correct_rejections: correctRejections,
        reaction_times: reactionTimes,
        hit_rate: hitRate,
        false_alarm_rate: falseAlarmRate,
        d_prime: dPrime,
        session_level: sessionLevel,
      },
    };
  }, [sessionLevel]);

  const finish = useCallback(() => {
    clearTimers();
    waitingRef.current = false;
    setStimulus("");
    setPhase("done");
    onRunStateChange?.(false);
    onComplete(buildMetricsFromTrials());
  }, [buildMetricsFromTrials, onComplete, onRunStateChange]);

  const runNextTrial = useCallback(() => {
    if (indexRef.current >= totalTrials) {
      finish();
      return;
    }

    const trial = trialsRef.current[indexRef.current];
    setDisplayIndex(indexRef.current + 1);
    stimulusStartRef.current = performance.now();
    waitingRef.current = true;
    setStimulus(trial.type === "go" ? "go" : "nogo");

    schedule(() => {
      if (!waitingRef.current) return;
      waitingRef.current = false;
      const t = trialsRef.current[indexRef.current];
      if (t.type === "go") {
        t.responded = false;
        t.correct = false;
        setStats((s) => ({ ...s, misses: s.misses + 1 }));
      } else {
        t.responded = false;
        t.correct = true;
        setStats((s) => ({ ...s, correctRejections: s.correctRejections + 1 }));
      }
      setStimulus("");
      indexRef.current += 1;
      schedule(() => runNextTrial(), isi);
    }, stimulusDuration);
  }, [finish, isi, stimulusDuration, totalTrials]);

  const handleResponse = useCallback(() => {
    if (!waitingRef.current) return;
    waitingRef.current = false;
    clearTimers();

    const rt = performance.now() - stimulusStartRef.current;
    const trial = trialsRef.current[indexRef.current];

    if (trial.type === "go") {
      trial.responded = true;
      trial.responseTime = rt;
      trial.correct = true;
      setStats((s) => ({
        ...s,
        hits: s.hits + 1,
        reactionTimes: [...s.reactionTimes, rt],
      }));
    } else {
      trial.responded = true;
      trial.responseTime = rt;
      trial.correct = false;
      setStats((s) => ({ ...s, falseAlarms: s.falseAlarms + 1 }));
    }

    setStimulus("");
    indexRef.current += 1;
    schedule(() => runNextTrial(), isi);
  }, [runNextTrial]);

  const startTest = () => {
    const trials: Trial[] = [];
    for (let i = 0; i < totalTrials; i++) {
      trials.push({
        type: Math.random() < goProbability ? "go" : "nogo",
        responded: false,
        responseTime: null,
        correct: false,
      });
    }
    shuffleTrials(trials);
    trialsRef.current = trials;
    indexRef.current = 0;
    setStats({
      hits: 0,
      misses: 0,
      falseAlarms: 0,
      correctRejections: 0,
      reactionTimes: [],
    });
    setPhase("running");
    onRunStateChange?.(true);
    runNextTrial();
  };

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (phase !== "running" || !waitingRef.current) return;
      const target = e.target as HTMLElement;
      if (target.closest("button")) return;
      handleResponse();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.code === "Space" && phase === "running" && waitingRef.current) {
        e.preventDefault();
        handleResponse();
      }
    };
    window.addEventListener("click", onClick);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("click", onClick);
      window.removeEventListener("keydown", onKey);
    };
  }, [phase, handleResponse]);

  useEffect(
    () => () => {
      clearTimers();
    },
    []
  );

  if (phase === "intro") {
    return (
      <BrutalCard accent="muted" className="assessment-task-intro">
        <h3 className="headline">Go / No-Go</h3>
        <p>
          When you see <span style={{ color: "#2e7d32", fontWeight: 700 }}>✓</span> (green), press Space or click the
          task area quickly.
        </p>
        <p>
          When you see <span style={{ color: "#c62828", fontWeight: 700 }}>✕</span> (red), do not respond.
        </p>
        <p className="small-copy">{totalTrials} trials — about 2–3 minutes.</p>
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

  const progress = (displayIndex / totalTrials) * 100;
  const avgRt =
    stats.reactionTimes.length > 0
      ? Math.round(stats.reactionTimes.reduce((a, b) => a + b, 0) / stats.reactionTimes.length)
      : 0;

  return (
    <BrutalCard accent="white" className="assessment-go-nogo">
      <div
        style={{
          height: 10,
          borderRadius: 6,
          background: "rgba(0,0,0,0.08)",
          overflow: "hidden",
          marginBottom: 12,
        }}
      >
        <div style={{ width: `${progress}%`, height: "100%", background: "linear-gradient(90deg,#4CAF50,#2196F3)" }} />
      </div>
      <div
        style={{
          minHeight: 160,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          userSelect: "none",
          cursor: "default",
        }}
      >
        {stimulus === "go" && (
          <span style={{ fontSize: "7rem", fontWeight: 800, color: "#2e7d32", lineHeight: 1 }}>✓</span>
        )}
        {stimulus === "nogo" && (
          <span style={{ fontSize: "7rem", fontWeight: 800, color: "#c62828", lineHeight: 1 }}>✕</span>
        )}
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 8,
          fontSize: 12,
          textAlign: "center",
        }}
      >
        <span>
          Trial {displayIndex}/{totalTrials}
        </span>
        <span>Hits: {stats.hits}</span>
        <span>Misses: {stats.misses}</span>
        <span>False alarms: {stats.falseAlarms}</span>
        <span>Correct rejections: {stats.correctRejections}</span>
        <span>Avg RT: {avgRt} ms</span>
      </div>
    </BrutalCard>
  );
};
