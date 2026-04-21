import React, { useCallback, useEffect, useRef, useState } from "react";

import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export interface PatternSwitchTaskProps {
  onComplete: (results: Record<string, unknown>) => void;
  onRunStateChange?: (running: boolean) => void;
  sessionLevel?: number;
}

type Rule = { type: "color" | "shape"; value: string; text: string };

type Target = {
  id: number;
  leftPct: number;
  topPct: number;
  size: number;
  color: string;
  shape: "circle" | "square";
  correct: boolean;
  spawnAt: number;
};

const RULES: Rule[] = [
  { type: "color", value: "blue", text: "Click BLUE targets" },
  { type: "color", value: "red", text: "Click RED targets" },
  { type: "color", value: "green", text: "Click GREEN targets" },
  { type: "color", value: "yellow", text: "Click YELLOW targets" },
  { type: "shape", value: "circle", text: "Click CIRCLE targets" },
  { type: "shape", value: "square", text: "Click SQUARE targets" },
];

const COLOR_MAP: Record<string, string> = {
  blue: "#667eea",
  red: "#f56565",
  green: "#48bb78",
  yellow: "#ed8936",
};

function pickRule(prev: Rule | null): Rule {
  let next: Rule;
  do {
    next = RULES[Math.floor(Math.random() * RULES.length)];
  } while (prev && next.type === prev.type && next.value === prev.value);
  return next;
}

export const PatternSwitchTask: React.FC<PatternSwitchTaskProps> = ({
  onComplete,
  onRunStateChange,
  sessionLevel = 1,
}) => {
  const [phase, setPhase] = useState<"intro" | "running" | "done">("intro");
  const [rule, setRule] = useState<Rule | null>(null);
  const [targets, setTargets] = useState<Target[]>([]);
  const [banner, setBanner] = useState(false);
  const [hud, setHud] = useState({ score: 0, level: 1, hits: 0, misses: 0, combo: 0, time: "0:00" });

  const areaRef = useRef<HTMLDivElement>(null);
  const spawnTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const clockRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const clearedTargetsRef = useRef(new Set<number>());
  const gameEndedRef = useRef(false);
  const gameRef = useRef({
    score: 0,
    level: 1,
    hits: 0,
    misses: 0,
    correctHits: 0,
    combo: 0,
    maxCombo: 0,
    spawnInterval: 2000,
    targetLifetime: 3000,
    ruleChangeThreshold: 5,
    hitsSinceRuleChange: 0,
    currentRule: null as Rule | null,
    ruleChanges: 0,
    errorsPerSwitch: [] as number[],
    trialData: [] as Record<string, unknown>[],
    consecutiveErrors: 0,
    maxConsecutiveErrors: 0,
    startedAt: 0,
    nextId: 1,
  });

  const clearGameTimers = () => {
    if (spawnTimeoutRef.current) {
      clearTimeout(spawnTimeoutRef.current);
      spawnTimeoutRef.current = null;
    }
    if (clockRef.current) {
      clearInterval(clockRef.current);
      clockRef.current = null;
    }
  };

  const shouldEnd = () => {
    const g = gameRef.current;
    return g.level > 10 || (g.misses > 20 && g.misses > g.hits * 2);
  };

  const syncHud = () => {
    const g = gameRef.current;
    setHud({
      score: g.score,
      level: g.level,
      hits: g.hits,
      misses: g.misses,
      combo: g.combo,
      time: (() => {
        const s = Math.floor((performance.now() - g.startedAt) / 1000);
        const m = Math.floor(s / 60);
        const r = s % 60;
        return `${m}:${String(r).padStart(2, "0")}`;
      })(),
    });
  };

  const buildMetrics = useCallback(() => {
    const g = gameRef.current;
    const totalTrials = g.hits + g.misses;
    const accuracy = totalTrials > 0 ? g.hits / totalTrials : 0;
    const correctHitsData = g.trialData.filter((t) => t.type === "correct_hit") as {
      responseTime: number;
    }[];
    const meanResponseTime =
      correctHitsData.length > 0
        ? correctHitsData.reduce((sum, t) => sum + t.responseTime, 0) / correctHitsData.length
        : 0;
    const rtVariance =
      correctHitsData.length > 1
        ? correctHitsData.reduce((sum, t) => sum + (t.responseTime - meanResponseTime) ** 2, 0) /
          (correctHitsData.length - 1)
        : 0;
    const halfway = Math.floor(correctHitsData.length / 2);
    const early = correctHitsData.slice(0, halfway);
    const late = correctHitsData.slice(halfway);
    const earlyAvg = early.length ? early.reduce((s, t) => s + t.responseTime, 0) / early.length : 0;
    const lateAvg = late.length ? late.reduce((s, t) => s + t.responseTime, 0) / late.length : 0;
    const performanceDecay = earlyAvg > 0 ? (lateAvg - earlyAvg) / earlyAvg : 0;
    const errorTrials = g.trialData.filter(
      (t, i) => i > 0 && g.trialData[i - 1].type === "incorrect_hit" && t.type === "correct_hit"
    );
    const totalErrors = g.trialData.filter((t) => t.type === "incorrect_hit").length;
    const recoverySlope = totalErrors > 0 ? errorTrials.length / totalErrors : 0;
    const adaptationQuality =
      g.errorsPerSwitch.length > 0
        ? 1 - g.errorsPerSwitch.reduce((a, b) => a + b, 0) / g.errorsPerSwitch.length / 10
        : 1;

    return {
      accuracy,
      mean_response_time: meanResponseTime,
      response_time_variance: rtVariance,
      performance_decay: performanceDecay,
      retry_depth: 1 - accuracy,
      dropout_depth_index: totalTrials > 0 ? g.misses / totalTrials : 0,
      recovery_slope: recoverySlope,
      raw: {
        total_trials: totalTrials,
        hits: g.hits,
        misses: g.misses,
        score: g.score,
        level: g.level,
        max_combo: g.maxCombo,
        rule_changes: g.ruleChanges,
        errors_per_switch: g.errorsPerSwitch,
        adaptation_quality: adaptationQuality,
        impulse_rate: totalTrials > 0 ? g.misses / totalTrials : 0,
        persistence_after_mistakes: g.maxConsecutiveErrors > 0 ? 1 / g.maxConsecutiveErrors : 1,
        max_consecutive_errors: g.maxConsecutiveErrors,
        trial_data: g.trialData,
        session_level: sessionLevel,
      },
    };
  }, [sessionLevel]);

  const endGame = useCallback(() => {
    gameEndedRef.current = true;
    clearGameTimers();
    setTargets([]);
    setPhase("done");
    onRunStateChange?.(false);
    onComplete(buildMetrics());
  }, [buildMetrics, onComplete, onRunStateChange]);

  const applyNewRule = (next: Rule, prev: Rule | null) => {
    const g = gameRef.current;
    g.currentRule = next;
    setRule(next);
    setBanner(true);
    setTimeout(() => setBanner(false), 2000);
    g.hitsSinceRuleChange = 0;
    if (prev) {
      g.ruleChanges++;
      g.errorsPerSwitch.push(g.consecutiveErrors);
      g.consecutiveErrors = 0;
    }
  };

  const spawnOne = useCallback(() => {
    if (gameEndedRef.current) return;
    if (shouldEnd()) {
      endGame();
      return;
    }
    const g = gameRef.current;
    const colors = ["blue", "red", "green", "yellow"] as const;
    const shapes: ("circle" | "square")[] = ["circle", "square"];
    const color = colors[Math.floor(Math.random() * colors.length)];
    const shape = shapes[Math.floor(Math.random() * shapes.length)];
    const r = g.currentRule;
    const correct =
      r!.type === "color" ? color === r!.value : shape === (r!.value as "circle" | "square");

    const area = areaRef.current;
    const w = area?.clientWidth ?? 400;
    const h = area?.clientHeight ?? 360;
    const size = 60 + Math.random() * 40;
    const maxX = Math.max(8, w - size - 16);
    const maxY = Math.max(8, h - size - 16);
    const leftPx = Math.random() * maxX;
    const topPx = 72 + Math.random() * Math.max(20, maxY - 72);

    const id = g.nextId++;
    const spawnAt = performance.now();
    const leftPct = (leftPx / w) * 100;
    const topPct = (topPx / h) * 100;

    const t: Target = { id, leftPct, topPct, size, color, shape, correct, spawnAt };
    setTargets((prev) => [...prev, t]);

    setTimeout(() => {
      if (clearedTargetsRef.current.has(id)) return;
      setTargets((prev) => prev.filter((x) => x.id !== id));
      if (correct) {
        g.misses++;
        g.combo = 0;
        syncHud();
        if (shouldEnd()) endGame();
      }
    }, g.targetLifetime);
  }, [endGame]);

  const scheduleSpawnLoop = useCallback(() => {
    const tick = () => {
      if (gameEndedRef.current) return;
      if (shouldEnd()) {
        endGame();
        return;
      }
      spawnOne();
      spawnTimeoutRef.current = setTimeout(tick, gameRef.current.spawnInterval);
    };
    tick();
  }, [endGame, spawnOne]);

  const onTargetClick = (target: Target) => {
    if (gameEndedRef.current) return;
    const g = gameRef.current;
    const rt = performance.now() - target.spawnAt;
    clearedTargetsRef.current.add(target.id);
    setTargets((prev) => prev.filter((x) => x.id !== target.id));

    if (target.correct) {
      g.hits++;
      g.correctHits++;
      g.hitsSinceRuleChange++;
      g.combo++;
      g.maxCombo = Math.max(g.maxCombo, g.combo);
      const points = Math.max(10, 50 - Math.floor(rt / 100));
      g.score += points * (1 + Math.floor(g.combo / 5));
      g.trialData.push({
        type: "correct_hit",
        responseTime: rt,
        rule: g.currentRule,
        combo: g.combo,
        points,
      });
      if (g.consecutiveErrors > 0) g.consecutiveErrors = 0;

      if (g.hitsSinceRuleChange >= g.ruleChangeThreshold) {
        const prev = g.currentRule;
        applyNewRule(pickRule(prev), prev);
      }

      if (g.correctHits > 0 && g.correctHits % 10 === 0) {
        g.level++;
        g.spawnInterval = Math.max(500, g.spawnInterval - 150);
        g.targetLifetime = Math.max(1500, g.targetLifetime - 100);
        g.ruleChangeThreshold = Math.max(3, g.ruleChangeThreshold - 1);
      }
    } else {
      g.misses++;
      g.combo = 0;
      g.consecutiveErrors++;
      g.maxConsecutiveErrors = Math.max(g.maxConsecutiveErrors, g.consecutiveErrors);
      g.score = Math.max(0, g.score - 20);
      g.trialData.push({
        type: "incorrect_hit",
        responseTime: rt,
        rule: g.currentRule,
        consecutiveErrors: g.consecutiveErrors,
      });
    }
    syncHud();
    if (shouldEnd()) endGame();
  };

  const start = () => {
    gameEndedRef.current = false;
    clearedTargetsRef.current = new Set();
    gameRef.current = {
      score: 0,
      level: 1,
      hits: 0,
      misses: 0,
      correctHits: 0,
      combo: 0,
      maxCombo: 0,
      spawnInterval: 2000,
      targetLifetime: 3000,
      ruleChangeThreshold: 5,
      hitsSinceRuleChange: 0,
      currentRule: null,
      ruleChanges: 0,
      errorsPerSwitch: [],
      trialData: [],
      consecutiveErrors: 0,
      maxConsecutiveErrors: 0,
      startedAt: performance.now(),
      nextId: 1,
    };
    const first = pickRule(null);
    applyNewRule(first, null);
    setTargets([]);
    setPhase("running");
    onRunStateChange?.(true);
    syncHud();
    clockRef.current = setInterval(syncHud, 200);
    scheduleSpawnLoop();
  };

  useEffect(
    () => () => {
      clearGameTimers();
    },
    []
  );

  if (phase === "intro") {
    return (
      <BrutalCard accent="muted" className="assessment-task-intro">
        <h3 className="headline">Pattern switch survival</h3>
        <p>Follow the rule in the header. Rules change after several correct hits.</p>
        <p className="small-copy">
          Click only targets that match the current rule. Wrong clicks and missed valid targets count against you.
        </p>
        <BrutalButton variant="primary" onClick={start} data-testid="task-start">
          Start survival
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

  const speeds = ["Normal", "Fast", "Very Fast", "Extreme", "Insane"];
  const speedLabel = speeds[Math.min(speeds.length - 1, Math.floor((hud.level - 1) / 2))];
  const acc = hud.hits + hud.misses > 0 ? ((hud.hits / (hud.hits + hud.misses)) * 100).toFixed(1) : "100";

  const pill: React.CSSProperties = {
    display: "inline-block",
    padding: "4px 10px",
    borderRadius: 999,
    fontSize: 12,
    background: "rgba(0,0,0,0.08)",
    marginRight: 6,
  };

  return (
    <BrutalCard accent="blue" className="assessment-pattern-switch">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 8,
          padding: "10px 0",
          borderBottom: "2px solid rgba(0,0,0,0.08)",
        }}
      >
        <div>
          <span style={pill}>Score: {hud.score}</span>
          <span style={pill}>Level: {hud.level}</span>
        </div>
        <div style={{ fontWeight: 700, flex: 1, textAlign: "center", minWidth: 200 }}>{rule?.text}</div>
        <div>
          <span style={pill}>Accuracy: {acc}%</span>
          <span style={pill}>Time: {hud.time}</span>
        </div>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0" }}>
        <span style={pill}>Speed: {speedLabel}</span>
        <span style={pill}>Combo ×{hud.combo}</span>
      </div>
      <div
        ref={areaRef}
        style={{
          position: "relative",
          height: 400,
          marginTop: 8,
          borderRadius: 8,
          background: "linear-gradient(135deg, rgba(102,126,234,0.35) 0%, rgba(118,75,162,0.35) 100%)",
          cursor: "crosshair",
          overflow: "hidden",
        }}
      >
        {banner && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 10,
              pointerEvents: "none",
              background: "rgba(0,0,0,0.15)",
            }}
          >
            <div style={{ padding: "16px 28px", borderRadius: 8, background: "#fff", textAlign: "center" }}>
              <div style={{ fontWeight: 800 }}>Rule change</div>
              <div>{rule?.text}</div>
            </div>
          </div>
        )}
        {targets.map((t) => (
          <button
            type="button"
            key={t.id}
            onClick={(e) => {
              e.stopPropagation();
              onTargetClick(t);
            }}
            style={{
              position: "absolute",
              left: `${t.leftPct}%`,
              top: `${t.topPct}%`,
              width: t.size,
              height: t.size,
              borderRadius: t.shape === "circle" ? "50%" : 8,
              background: COLOR_MAP[t.color] ?? "#999",
              border: "none",
              cursor: "pointer",
              boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
            }}
          />
        ))}
      </div>
    </BrutalCard>
  );
};
