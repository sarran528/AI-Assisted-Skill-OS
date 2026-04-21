import React, { useCallback, useEffect, useId, useRef, useState } from "react";

import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export interface CountdownChallengeTaskProps {
  onComplete: (results: Record<string, unknown>) => void;
  onRunStateChange?: (running: boolean) => void;
  sessionLevel?: number;
}

type QType = "numberCompare" | "arithmetic" | "patternMatch";

interface Question {
  type: QType;
  text: string;
  options: string[];
  correct: string;
}

function generateWrongAnswers(correct: number, count: number): string[] {
  const options = [String(correct)];
  const used = new Set<number>([correct]);
  while (options.length < count) {
    const variance = Math.max(10, Math.floor(correct * 0.3));
    const wrong =
      Math.random() < 0.5
        ? correct + Math.floor(Math.random() * variance) + 1
        : Math.max(0, correct - Math.floor(Math.random() * variance) - 1);
    if (!used.has(wrong)) {
      used.add(wrong);
      options.push(String(wrong));
    }
  }
  return options;
}

function buildQuestion(): Question {
  const types: QType[] = ["numberCompare", "arithmetic", "patternMatch"];
  const type = types[Math.floor(Math.random() * types.length)];
  if (type === "numberCompare") {
    const a = Math.floor(Math.random() * 100) + 1;
    const b = Math.floor(Math.random() * 100) + 1;
    return {
      type,
      text: `Which is larger: ${a} or ${b}?`,
      options: [String(a), String(b)].sort(() => Math.random() - 0.5),
      correct: String(a > b ? a : b),
    };
  }
  if (type === "arithmetic") {
    const ops = ["+", "-", "*"] as const;
    const op = ops[Math.floor(Math.random() * ops.length)];
    let a = 0;
    let b = 0;
    let result = 0;
    if (op === "+") {
      a = Math.floor(Math.random() * 50) + 1;
      b = Math.floor(Math.random() * 50) + 1;
      result = a + b;
    } else if (op === "-") {
      a = Math.floor(Math.random() * 50) + 20;
      b = Math.floor(Math.random() * a);
      result = a - b;
    } else {
      a = Math.floor(Math.random() * 12) + 1;
      b = Math.floor(Math.random() * 12) + 1;
      result = a * b;
    }
    const sym = op === "*" ? "×" : op;
    return {
      type,
      text: `${a} ${sym} ${b} = ?`,
      options: generateWrongAnswers(result, 4).sort(() => Math.random() - 0.5),
      correct: String(result),
    };
  }
  const patterns = [
    { sequence: [2, 4, 6, 8], answer: 10 },
    { sequence: [1, 3, 5, 7], answer: 9 },
    { sequence: [5, 10, 15, 20], answer: 25 },
    { sequence: [3, 6, 9, 12], answer: 15 },
    { sequence: [1, 4, 9, 16], answer: 25 },
  ];
  const p = patterns[Math.floor(Math.random() * patterns.length)];
  return {
    type: "patternMatch",
    text: `Complete the pattern: ${p.sequence.join(", ")}, ?`,
    options: generateWrongAnswers(p.answer, 4).sort(() => Math.random() - 0.5),
    correct: String(p.answer),
  };
}

const R = 80;
const CIRC = 2 * Math.PI * R;

export const CountdownChallengeTask: React.FC<CountdownChallengeTaskProps> = ({
  onComplete,
  onRunStateChange,
  sessionLevel = 1,
}) => {
  const gradId = useId().replace(/:/g, "");
  const [phase, setPhase] = useState<"intro" | "running" | "done">("intro");
  const [q, setQ] = useState<Question | null>(null);
  const [timeLeftMs, setTimeLeftMs] = useState(3000);
  const [timeLimit, setTimeLimit] = useState(3000);
  const [level, setLevel] = useState(1);
  const [streak, setStreak] = useState(0);
  const [hud, setHud] = useState({ correct: 0, errors: 0, avg: 0, acc: "100.0" });
  const [picked, setPicked] = useState<string | null>(null);
  const [flashTimeout, setFlashTimeout] = useState(false);

  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const advanceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const gameRef = useRef({
    correct: 0,
    errors: 0,
    streak: 0,
    maxStreak: 0,
    level: 1,
    timeLimit: 3000,
    minTimeLimit: 800,
    timeDecrement: 80,
    responseTimes: [] as number[],
    trialData: [] as Record<string, unknown>[],
    consecutiveErrors: 0,
    pressureBreakpoint: null as number | null,
    recoveryAttempts: [] as { errorsBefore: number; recoveryTime: number; level: number }[],
    questionStart: 0,
    currentQuestion: null as Question | null,
    answered: false,
  });

  const clearCountdown = () => {
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
    if (advanceRef.current) {
      clearTimeout(advanceRef.current);
      advanceRef.current = null;
    }
  };

  const syncHud = () => {
    const g = gameRef.current;
    const total = g.correct + g.errors;
    const acc = total > 0 ? ((g.correct / total) * 100).toFixed(1) : "100.0";
    const avg =
      g.responseTimes.length > 0
        ? Math.round(g.responseTimes.reduce((a, b) => a + b, 0) / g.responseTimes.length)
        : 0;
    setHud({ correct: g.correct, errors: g.errors, avg, acc });
    setLevel(g.level);
    setStreak(g.streak);
    setTimeLimit(g.timeLimit);
  };

  const shouldEnd = () => {
    const g = gameRef.current;
    return g.trialData.length >= 30 || (g.errors > 15 && g.errors > g.correct * 2);
  };

  const buildMetrics = useCallback(() => {
    const g = gameRef.current;
    const total = g.correct + g.errors;
    const accuracy = total > 0 ? g.correct / total : 0;
    const meanResponseTime =
      g.responseTimes.length > 0 ? g.responseTimes.reduce((a, b) => a + b, 0) / g.responseTimes.length : 0;
    const rtVar =
      g.responseTimes.length > 1
        ? g.responseTimes.reduce((s, rt) => s + (rt - meanResponseTime) ** 2, 0) / (g.responseTimes.length - 1)
        : 0;
    const half = Math.floor(g.responseTimes.length / 2);
    const fh = g.responseTimes.slice(0, half);
    const sh = g.responseTimes.slice(half);
    const fa = fh.length ? fh.reduce((a, b) => a + b, 0) / fh.length : 0;
    const sa = sh.length ? sh.reduce((a, b) => a + b, 0) / sh.length : 0;
    const performanceDecay = fa > 0 ? (sa - fa) / fa : 0;
    const recoverySlope =
      g.recoveryAttempts.length > 0
        ? g.recoveryAttempts.reduce((sum, r) => sum + 1 / r.errorsBefore, 0) / g.recoveryAttempts.length
        : 0;
    const avgLimit = g.trialData.length
      ? (g.trialData as { timeLimit: number }[]).reduce((s, t) => s + t.timeLimit, 0) / g.trialData.length
      : 3000;
    const timePressure = 1 - avgLimit / 3000;

    return {
      accuracy,
      mean_response_time: meanResponseTime,
      response_time_variance: rtVar,
      performance_decay: performanceDecay,
      retry_depth: 1 - accuracy,
      dropout_depth_index: total > 0 ? g.errors / total : 0,
      recovery_slope: recoverySlope,
      raw: {
        total_trials: g.trialData.length,
        correct: g.correct,
        errors: g.errors,
        max_streak: g.maxStreak,
        level_reached: g.level,
        pressure_breakpoint: g.pressureBreakpoint ?? g.trialData.length,
        recovery_attempts: g.recoveryAttempts,
        consecutive_errors: g.consecutiveErrors,
        time_pressure: timePressure,
        final_time_limit: g.timeLimit,
        response_times: g.responseTimes,
        trial_data: g.trialData,
        session_level: sessionLevel,
      },
    };
  }, [sessionLevel]);

  const finish = useCallback(() => {
    clearCountdown();
    setPhase("done");
    onRunStateChange?.(false);
    onComplete(buildMetrics());
  }, [buildMetrics, onComplete, onRunStateChange]);

  const goNextQuestionRef = useRef<() => void>(() => {});

  const goNextQuestion = useCallback(() => {
    if (advanceRef.current) {
      clearTimeout(advanceRef.current);
      advanceRef.current = null;
    }
    if (shouldEnd()) {
      finish();
      return;
    }
    const nq = buildQuestion();
    const g = gameRef.current;
    g.currentQuestion = nq;
    g.answered = false;
    g.questionStart = performance.now();
    setQ(nq);
    setPicked(null);
    setFlashTimeout(false);
    setTimeLeftMs(g.timeLimit);

    if (countdownRef.current) clearInterval(countdownRef.current);
    countdownRef.current = setInterval(() => {
      const gg = gameRef.current;
      if (gg.answered) return;
      setTimeLeftMs((prev) => {
        const next = Math.max(0, prev - 20);
        if (next <= 0 && countdownRef.current) {
          clearInterval(countdownRef.current);
          countdownRef.current = null;
          runTimeout();
        }
        return next;
      });
    }, 20);
  }, [finish]);

  const runTimeout = () => {
    const g = gameRef.current;
    if (g.answered || !g.currentQuestion) return;
    g.answered = true;
    const question = g.currentQuestion;
    setFlashTimeout(true);
    g.trialData.push({
      trial: g.trialData.length + 1,
      type: question.type,
      question: question.text,
      correctAnswer: question.correct,
      userAnswer: null,
      isCorrect: false,
      responseTime: g.timeLimit,
      timeLimit: g.timeLimit,
      level: g.level,
      timeout: true,
    });
    g.errors++;
    g.streak = 0;
    g.consecutiveErrors++;
    if (g.pressureBreakpoint === null && g.consecutiveErrors >= 2) {
      g.pressureBreakpoint = g.trialData.length;
    }
    syncHud();
    advanceRef.current = setTimeout(() => {
      goNextQuestionRef.current();
    }, 1500);
  };

  goNextQuestionRef.current = goNextQuestion;

  const handlePick = (answer: string) => {
    const g = gameRef.current;
    if (g.answered || !g.currentQuestion) return;
    g.answered = true;
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
    const question = g.currentQuestion;
    setPicked(answer);
    const rt = performance.now() - g.questionStart;
    const ok = answer === question.correct;
    g.trialData.push({
      trial: g.trialData.length + 1,
      type: question.type,
      question: question.text,
      correctAnswer: question.correct,
      userAnswer: answer,
      isCorrect: ok,
      responseTime: rt,
      timeLimit: g.timeLimit,
      level: g.level,
    });
    if (ok) {
      g.correct++;
      g.streak++;
      g.maxStreak = Math.max(g.maxStreak, g.streak);
      g.responseTimes.push(rt);
      if (g.consecutiveErrors > 0) {
        g.recoveryAttempts.push({ errorsBefore: g.consecutiveErrors, recoveryTime: rt, level: g.level });
      }
      g.consecutiveErrors = 0;
      if (g.correct > 0 && g.correct % 5 === 0) {
        g.level++;
        g.timeLimit = Math.max(g.minTimeLimit, g.timeLimit - g.timeDecrement);
      }
    } else {
      g.errors++;
      g.streak = 0;
      g.consecutiveErrors++;
      if (g.pressureBreakpoint === null && g.consecutiveErrors >= 2) {
        g.pressureBreakpoint = g.trialData.length;
      }
    }
    syncHud();
    advanceRef.current = setTimeout(() => {
      goNextQuestionRef.current();
    }, 1500);
  };

  useEffect(() => () => clearCountdown(), []);

  const start = () => {
    gameRef.current = {
      correct: 0,
      errors: 0,
      streak: 0,
      maxStreak: 0,
      level: 1,
      timeLimit: 3000,
      minTimeLimit: 800,
      timeDecrement: 80,
      responseTimes: [],
      trialData: [],
      consecutiveErrors: 0,
      pressureBreakpoint: null,
      recoveryAttempts: [],
      questionStart: 0,
      currentQuestion: null,
      answered: false,
    };
    syncHud();
    setPhase("running");
    onRunStateChange?.(true);
    goNextQuestion();
  };

  if (phase === "intro") {
    return (
      <BrutalCard accent="muted" className="assessment-task-intro">
        <h3 className="headline">Countdown adaptive challenge</h3>
        <p>Answer each question before the ring timer expires. Time pressure increases as you level up.</p>
        <BrutalButton variant="primary" onClick={start} data-testid="task-start">
          Start challenge
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

  const progress = timeLimit > 0 ? timeLeftMs / timeLimit : 0;
  const offset = CIRC - progress * CIRC;
  const digitColor =
    timeLeftMs < 1000 ? "#c62828" : timeLeftMs < 2000 ? "#f57c00" : "#2e7d32";

  const pill: React.CSSProperties = {
    display: "inline-block",
    padding: "4px 10px",
    borderRadius: 999,
    fontSize: 12,
    background: "rgba(0,0,0,0.08)",
    marginRight: 6,
  };

  return (
    <BrutalCard accent="white" className="assessment-countdown">
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
        <span style={pill}>Correct: {hud.correct}</span>
        <span style={pill}>Errors: {hud.errors}</span>
        <span style={pill}>Avg: {hud.avg} ms</span>
        <span style={pill}>Accuracy: {hud.acc}%</span>
        <span style={pill}>Level {level}</span>
        <span style={pill}>Streak: {streak}</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
        <div style={{ position: "relative", width: 200, height: 200 }}>
          <svg width={200} height={200} style={{ transform: "rotate(-90deg)" }}>
            <defs>
              <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#4CAF50" />
                <stop offset="100%" stopColor="#f44336" />
              </linearGradient>
            </defs>
            <circle cx={100} cy={100} r={R} fill="none" stroke="rgba(0,0,0,0.12)" strokeWidth={20} />
            <circle
              cx={100}
              cy={100}
              r={R}
              fill="none"
              stroke={`url(#${gradId})`}
              strokeWidth={20}
              strokeLinecap="round"
              strokeDasharray={`${CIRC} ${CIRC}`}
              style={{ strokeDashoffset: offset, transition: "stroke-dashoffset 0.05s linear" }}
            />
          </svg>
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "2.5rem",
              fontWeight: 800,
              color: digitColor,
            }}
          >
            {(timeLeftMs / 1000).toFixed(1)}
          </div>
        </div>
        {flashTimeout && (
          <p style={{ color: "#c62828", fontWeight: 800, margin: 0 }}>
            Time&apos;s up
          </p>
        )}
        {q && (
          <div
            style={{
              border: "2px solid rgba(0,0,0,0.12)",
              borderRadius: 12,
              padding: 16,
              width: "100%",
              textAlign: "center",
            }}
          >
            <h4 style={{ marginTop: 0 }}>{q.text}</h4>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 8,
              }}
            >
              {q.options.map((opt) => {
                const showCorrect = picked != null && opt === q.correct;
                const showWrong = picked != null && opt === picked && picked !== q.correct;
                return (
                  <BrutalButton
                    key={opt}
                    type="button"
                    variant={showCorrect ? "primary" : showWrong ? "danger" : "secondary"}
                    disabled={picked != null}
                    onClick={() => handlePick(opt)}
                    style={{ padding: "16px 8px", fontSize: "1.05rem" }}
                  >
                    {opt}
                  </BrutalButton>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </BrutalCard>
  );
};
