import React, { useCallback, useEffect, useRef, useState } from "react";

import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export interface RapidTapTaskProps {
  onComplete: (results: Record<string, unknown>) => void;
  onRunStateChange?: (running: boolean) => void;
  sessionLevel?: number;
}

type TrialRow = {
  trial: number;
  reactionTime: number | null;
  targetSize: number;
  level: number;
  combo: number;
  points: number;
  correct: boolean;
};

const TARGET_SIZES = [70, 60, 50, 40, 36, 30, 25, 20];

export const RapidTapTask: React.FC<RapidTapTaskProps> = ({
  onComplete,
  onRunStateChange,
  sessionLevel = 1,
}) => {
  const maxTargets = 30;

  const [phase, setPhase] = useState<"intro" | "running" | "done">("intro");
  const [target, setTarget] = useState<{ leftPct: number; topPct: number; size: number } | null>(null);
  const [hud, setHud] = useState({
    hits: 0,
    misses: 0,
    combo: 0,
    level: 1,
    avgRt: 0,
    accuracy: "100.0",
    progress: 0,
    timer: "0:00",
    difficulty: "Easy",
  });

  const areaRef = useRef<HTMLDivElement>(null);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const hudIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const gameRef = useRef({
    hits: 0,
    misses: 0,
    combo: 0,
    maxCombo: 0,
    level: 1,
    score: 0,
    reactionTimes: [] as number[],
    trialData: [] as TrialRow[],
    currentTargetCount: 0,
    targetLifetime: 3000,
    spawnInterval: 2000,
    spawnAt: 0,
    currentSize: 70,
    gameStart: 0,
    missTimer: null as ReturnType<typeof setTimeout> | null,
  });

  const clearTimers = () => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
    if (hudIntervalRef.current) {
      clearInterval(hudIntervalRef.current);
      hudIntervalRef.current = null;
    }
    if (gameRef.current.missTimer) {
      clearTimeout(gameRef.current.missTimer);
      gameRef.current.missTimer = null;
    }
  };

  const schedule = (fn: () => void, ms: number) => {
    const id = setTimeout(() => {
      timersRef.current = timersRef.current.filter((t) => t !== id);
      fn();
    }, ms);
    timersRef.current.push(id);
  };

  const syncHud = () => {
    const g = gameRef.current;
    const total = g.hits + g.misses;
    const avg =
      g.reactionTimes.length > 0 ? g.reactionTimes.reduce((a, b) => a + b, 0) / g.reactionTimes.length : 0;
    const acc = total > 0 ? ((g.hits / total) * 100).toFixed(1) : "100.0";
    const elapsed = Math.floor((performance.now() - g.gameStart) / 1000);
    const difficulties = ["Easy", "Medium", "Hard", "Expert", "Master", "Legendary"];
    const diffIndex = Math.min(difficulties.length - 1, Math.floor((g.level - 1) / 2));
    setHud({
      hits: g.hits,
      misses: g.misses,
      combo: g.combo,
      level: g.level,
      avgRt: Math.round(avg),
      accuracy: acc,
      progress: (g.currentTargetCount / maxTargets) * 100,
      timer: `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, "0")}`,
      difficulty: difficulties[diffIndex],
    });
  };

  const buildMetrics = useCallback(() => {
    const g = gameRef.current;
    const totalAttempts = g.hits + g.misses;
    const accuracy = totalAttempts > 0 ? g.hits / totalAttempts : 0;
    const meanResponseTime =
      g.reactionTimes.length > 0 ? g.reactionTimes.reduce((a, b) => a + b, 0) / g.reactionTimes.length : 0;
    const rtVariance =
      g.reactionTimes.length > 1
        ? g.reactionTimes.reduce((sum, rt) => sum + (rt - meanResponseTime) ** 2, 0) / (g.reactionTimes.length - 1)
        : 0;
    const halfway = Math.floor(g.reactionTimes.length / 2);
    const fh = g.reactionTimes.slice(0, halfway);
    const sh = g.reactionTimes.slice(halfway);
    const fa = fh.length ? fh.reduce((a, b) => a + b, 0) / fh.length : 0;
    const sa = sh.length ? sh.reduce((a, b) => a + b, 0) / sh.length : 0;
    const performanceDecay = fa > 0 ? (sa - fa) / fa : 0;
    const missTrials = g.trialData.filter((t, i) => i > 0 && !g.trialData[i - 1].correct && t.correct);
    const totalMisses = g.trialData.filter((t) => !t.correct).length;
    const recoverySlope = totalMisses > 0 ? missTrials.length / totalMisses : 0;
    const reactionSpeed = meanResponseTime > 0 ? Math.max(0, 100 - meanResponseTime / 20) : 0;
    const motorPrecision = accuracy * 100;
    const movementStability = rtVariance > 0 ? Math.max(0, 100 - rtVariance / 100) : 100;
    const motorConsistency =
      g.reactionTimes.length > 1 ? Math.max(0, 100 - (rtVariance / meanResponseTime) * 10) : 100;
    const durSec = Math.max(0.001, (performance.now() - g.gameStart) / 1000);

    return {
      accuracy,
      mean_response_time: meanResponseTime,
      response_time_variance: rtVariance,
      performance_decay: performanceDecay,
      retry_depth: 1 - accuracy,
      dropout_depth_index: totalAttempts > 0 ? g.misses / totalAttempts : 0,
      recovery_slope: recoverySlope,
      raw: {
        total_targets: maxTargets,
        hits: g.hits,
        misses: g.misses,
        score: g.score,
        max_combo: g.maxCombo,
        level_reached: g.level,
        reaction_times: g.reactionTimes,
        target_sizes: g.trialData.map((t) => t.targetSize),
        reaction_speed: reactionSpeed,
        motor_precision: motorPrecision,
        movement_stability: movementStability,
        motor_consistency: motorConsistency,
        tap_speed_per_sec: g.hits / durSec,
        trial_data: g.trialData,
        session_level: sessionLevel,
      },
    };
  }, [sessionLevel]);

  const finish = useCallback(() => {
    clearTimers();
    setTarget(null);
    setPhase("done");
    onRunStateChange?.(false);
    onComplete(buildMetrics());
  }, [buildMetrics, onComplete, onRunStateChange]);

  const spawnTarget = useCallback(() => {
    const g = gameRef.current;
    if (g.currentTargetCount >= maxTargets) {
      finish();
      return;
    }
    const area = areaRef.current;
    const w = area?.clientWidth ?? 400;
    const h = area?.clientHeight ?? 380;
    const sizeIndex = Math.min(Math.floor((g.level - 1) / 4), TARGET_SIZES.length - 1);
    const size = TARGET_SIZES[sizeIndex];
    g.currentSize = size;
    const maxX = Math.max(8, w - size);
    const maxY = Math.max(8, h - size - 24);
    const leftPct = (Math.random() * maxX) / w * 100;
    const topPct = (48 + Math.random() * Math.max(10, maxY - 48)) / h * 100;
    g.spawnAt = performance.now();
    g.currentTargetCount += 1;
    setTarget({ leftPct, topPct, size });

    if (g.missTimer) clearTimeout(g.missTimer);
    g.missTimer = setTimeout(() => {
      g.misses++;
      g.combo = 0;
      g.trialData.push({
        trial: g.currentTargetCount,
        reactionTime: null,
        targetSize: size,
        level: g.level,
        combo: 0,
        points: 0,
        correct: false,
      });
      setTarget(null);
      syncHud();
      const avg = g.reactionTimes.length
        ? g.reactionTimes.reduce((a, b) => a + b, 0) / g.reactionTimes.length
        : 1000;
      g.spawnInterval = Math.max(800, 2000 - avg);
      schedule(() => spawnTarget(), g.spawnInterval);
    }, g.targetLifetime);
  }, [finish, maxTargets]);

  const handleHit = () => {
    const g = gameRef.current;
    if (!target) return;
    if (g.missTimer) {
      clearTimeout(g.missTimer);
      g.missTimer = null;
    }
    const rt = performance.now() - g.spawnAt;
    g.hits++;
    g.combo++;
    g.maxCombo = Math.max(g.maxCombo, g.combo);
    g.reactionTimes.push(rt);
    const speedBonus = Math.max(0, 100 - Math.floor(rt / 10));
    const comboBonus = g.combo * 5;
    const sizeBonus = Math.floor((70 - g.currentSize) * 2);
    const points = speedBonus + comboBonus + sizeBonus;
    g.score += points;
    g.trialData.push({
      trial: g.currentTargetCount,
      reactionTime: rt,
      targetSize: g.currentSize,
      level: g.level,
      combo: g.combo,
      points,
      correct: true,
    });
    if (g.hits % 5 === 0) {
      g.level++;
      g.targetLifetime = Math.max(1500, g.targetLifetime - 100);
    }
    const avg = g.reactionTimes.reduce((a, b) => a + b, 0) / g.reactionTimes.length;
    g.spawnInterval = Math.max(800, 2000 - avg);
    setTarget(null);
    syncHud();
    schedule(() => spawnTarget(), 300 + g.spawnInterval);
  };

  const start = () => {
    clearTimers();
    gameRef.current = {
      hits: 0,
      misses: 0,
      combo: 0,
      maxCombo: 0,
      level: 1,
      score: 0,
      reactionTimes: [],
      trialData: [],
      currentTargetCount: 0,
      targetLifetime: 3000,
      spawnInterval: 2000,
      spawnAt: 0,
      currentSize: 70,
      gameStart: performance.now(),
      missTimer: null,
    };
    setPhase("running");
    onRunStateChange?.(true);
    syncHud();
    hudIntervalRef.current = setInterval(syncHud, 250);
    spawnTarget();
  };

  useEffect(
    () => () => {
      clearTimers();
    },
    []
  );

  if (phase === "intro") {
    return (
      <BrutalCard accent="muted" className="assessment-task-intro">
        <h3 className="headline">Rapid tap reflex</h3>
        <p>Tap each green target as quickly as you can before it disappears.</p>
        <p className="small-copy">{maxTargets} targets. Difficulty increases as you improve.</p>
        <BrutalButton variant="primary" onClick={start} data-testid="task-start">
          Start reflex test
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

  const pill: React.CSSProperties = {
    display: "inline-block",
    padding: "4px 10px",
    borderRadius: 999,
    fontSize: 12,
    background: "rgba(0,0,0,0.08)",
    marginRight: 6,
  };

  return (
    <BrutalCard accent="white" className="assessment-rapid-tap">
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8 }}>
        <span style={pill}>Hits: {hud.hits}</span>
        <span style={pill}>Misses: {hud.misses}</span>
        <span style={pill}>Avg: {hud.avgRt} ms</span>
        <span style={pill}>Accuracy: {hud.accuracy}%</span>
        <span style={pill}>{hud.timer}</span>
      </div>
      <p style={{ textAlign: "center", fontSize: 13 }}>
        Level {hud.level} — {hud.difficulty}
      </p>
      <div
        style={{
          height: 8,
          borderRadius: 6,
          background: "rgba(0,0,0,0.08)",
          overflow: "hidden",
          marginBottom: 8,
        }}
      >
        <div style={{ width: `${hud.progress}%`, height: "100%", background: "linear-gradient(90deg,#f48fb1,#e53935)" }} />
      </div>
      <div
        ref={areaRef}
        style={{
          position: "relative",
          height: 400,
          borderRadius: 8,
          background: "radial-gradient(circle at center, rgba(255,255,255,0.12) 0%, transparent 70%)",
          backgroundColor: "rgba(0,0,0,0.05)",
          overflow: "hidden",
        }}
      >
        {target && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              handleHit();
            }}
            style={{
              position: "absolute",
              left: `${target.leftPct}%`,
              top: `${target.topPct}%`,
              width: target.size,
              height: target.size,
              borderRadius: "50%",
              cursor: "pointer",
              border: "3px solid rgba(255,255,255,0.85)",
              background: "radial-gradient(circle, #4CAF50, #2e7d32)",
              boxShadow: "0 0 20px rgba(76,175,80,0.55)",
            }}
          />
        )}
      </div>
      <p style={{ textAlign: "center", marginTop: 8, fontSize: 13 }}>Combo ×{hud.combo}</p>
    </BrutalCard>
  );
};
