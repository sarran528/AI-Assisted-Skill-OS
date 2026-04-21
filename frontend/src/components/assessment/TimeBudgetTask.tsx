import React, { useCallback, useMemo, useState } from "react";

import { BrutalButton } from "../brutal/BrutalButton";
import { BrutalCard } from "../brutal/BrutalCard";

export interface TimeBudgetTaskProps {
  onComplete: (results: Record<string, unknown>) => void;
  onRunStateChange?: (running: boolean) => void;
  sessionLevel?: number;
}

type Priority = "high" | "medium" | "low";

interface TaskItem {
  id: number;
  name: string;
  hours: number;
  priority: Priority;
  description: string;
  isDisruption?: boolean;
}

const TEMPLATES: Omit<TaskItem, "id" | "hours">[] = [
  { name: "Project Development", priority: "high", description: "Core project work" },
  { name: "Team Meetings", priority: "high", description: "Weekly team sync" },
  { name: "Code Review", priority: "medium", description: "Review PRs" },
  { name: "Documentation", priority: "medium", description: "Update docs" },
  { name: "Learning", priority: "low", description: "Skill development" },
  { name: "Email & Admin", priority: "low", description: "Daily admin tasks" },
  { name: "Client Calls", priority: "high", description: "Client meetings" },
  { name: "Testing", priority: "medium", description: "QA and testing" },
  { name: "Research", priority: "low", description: "Market research" },
  { name: "Planning", priority: "medium", description: "Sprint planning" },
  { name: "Mentoring", priority: "low", description: "Team mentoring" },
  { name: "Bug Fixes", priority: "high", description: "Critical fixes" },
];

const DISRUPTIONS: Omit<TaskItem, "id">[] = [
  { name: "Emergency Bug Fix", hours: 4, priority: "high", description: "Critical production issue", isDisruption: true },
  { name: "Client Emergency", hours: 3, priority: "high", description: "Urgent client request", isDisruption: true },
  { name: "Server Maintenance", hours: 2, priority: "high", description: "Unscheduled maintenance", isDisruption: true },
  { name: "Security Update", hours: 3, priority: "high", description: "Critical security patch", isDisruption: true },
];

export const TimeBudgetTask: React.FC<TimeBudgetTaskProps> = ({
  onComplete,
  onRunStateChange,
  sessionLevel = 1,
}) => {
  const maxRounds = 3;
  const budgets = [20, 18, 15];

  const [phase, setPhase] = useState<"intro" | "running" | "done">("intro");
  const [round, setRound] = useState(1);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [dropped, setDropped] = useState<Set<number>>(new Set());
  const [toast, setToast] = useState<string | null>(null);
  const [disruptionAlert, setDisruptionAlert] = useState<string | null>(null);

  const [decisionCount, setDecisionCount] = useState(0);
  const [revisionCount, setRevisionCount] = useState(0);
  const [roundData, setRoundData] = useState<
    {
      round: number;
      budget: number;
      selectedTasks: number[];
      droppedTasks: number[];
      totalSelected: number;
      highPrioritySelected: number;
      totalHighPriority: number;
      decisions: number;
      revisions: number;
    }[]
  >([]);
  const [agg, setAgg] = useState({
    planning_efficiency: [] as number[],
    overcommit_rate: [] as number[],
    tradeoff_quality: [] as number[],
  });

  const currentBudget = budgets[round - 1];

  const totalSelectedHours = useMemo(() => {
    let sum = 0;
    selected.forEach((id) => {
      const t = tasks.find((x) => x.id === id);
      if (t) sum += t.hours;
    });
    return sum;
  }, [tasks, selected]);

  const breakdown = useMemo(() => {
    let high = 0;
    let medium = 0;
    let low = 0;
    selected.forEach((id) => {
      const t = tasks.find((x) => x.id === id);
      if (!t) return;
      if (t.priority === "high") high += t.hours;
      else if (t.priority === "medium") medium += t.hours;
      else low += t.hours;
    });
    return { high, medium, low };
  }, [tasks, selected]);

  const remaining = currentBudget - totalSelectedHours;
  const totalHigh = tasks.filter((t) => t.priority === "high").length;
  const selectedHigh = tasks.filter((t) => t.priority === "high" && selected.has(t.id)).length;
  const efficiencyPct = totalHigh > 0 ? ((selectedHigh / totalHigh) * 100).toFixed(1) : "0";

  const generateTasks = useCallback(() => {
    const shuffled = [...TEMPLATES].sort(() => Math.random() - 0.5);
    const count = 8 + Math.floor(Math.random() * 4);
    const next: TaskItem[] = [];
    for (let i = 0; i < count; i++) {
      const base = shuffled[i % shuffled.length];
      const hours = 2 + Math.floor(Math.random() * 8);
      next.push({
        id: i,
        name: base.name,
        priority: base.priority,
        description: base.description,
        hours: Math.max(1, hours),
      });
    }
    setTasks(next);
    setSelected(new Set());
    setDropped(new Set());
  }, []);

  const start = () => {
    setRound(1);
    setRoundData([]);
    setAgg({ planning_efficiency: [], overcommit_rate: [], tradeoff_quality: [] });
    setDecisionCount(0);
    setRevisionCount(0);
    generateTasks();
    setPhase("running");
    onRunStateChange?.(true);
  };

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2800);
  };

  React.useEffect(() => {
    if (phase !== "running" || round <= 1) return;
    const t = window.setTimeout(() => {
      const d = DISRUPTIONS[Math.floor(Math.random() * DISRUPTIONS.length)];
      const label = d.name;
      setTasks((prev) => {
        const id = prev.length ? Math.max(...prev.map((p) => p.id)) + 1 : 0;
        return [...prev, { ...d, id }];
      });
      setDisruptionAlert(label);
      setTimeout(() => setDisruptionAlert(null), 3000);
    }, 3000);
    return () => clearTimeout(t);
  }, [phase, round]);

  const toggleTask = (id: number) => {
    setDecisionCount((c) => c + 1);
    if (selected.has(id)) {
      setSelected((s) => {
        const n = new Set(s);
        n.delete(id);
        return n;
      });
      setDropped((s) => new Set(s).add(id));
      setRevisionCount((c) => c + 1);
    } else if (dropped.has(id)) {
      setDropped((s) => {
        const n = new Set(s);
        n.delete(id);
        return n;
      });
      setSelected((s) => new Set(s).add(id));
      setRevisionCount((c) => c + 1);
    } else {
      setSelected((s) => new Set(s).add(id));
    }
  };

  const clearSelection = () => {
    setSelected(new Set());
    setDropped(new Set());
    setRevisionCount((c) => c + 1);
  };

  const autoOptimize = () => {
    const order: Record<Priority, number> = { high: 0, medium: 1, low: 2 };
    const sorted = [...tasks].sort((a, b) => {
      if (order[a.priority] !== order[b.priority]) return order[a.priority] - order[b.priority];
      return a.hours - b.hours;
    });
    let budget = currentBudget;
    const sel = new Set<number>();
    const drop = new Set<number>();
    for (const t of sorted) {
      if (t.hours <= budget) {
        sel.add(t.id);
        budget -= t.hours;
      } else {
        drop.add(t.id);
      }
    }
    setSelected(sel);
    setDropped(drop);
    setRevisionCount((c) => c + 1);
    showToast("Tasks optimized for priority and efficiency");
  };

  const confirmSelection = () => {
    if (totalSelectedHours > currentBudget) {
      showToast("Selection exceeds budget. Drop some tasks.");
      return;
    }
    const highSel = tasks.filter((t) => t.priority === "high" && selected.has(t.id)).length;
    const highTot = tasks.filter((t) => t.priority === "high").length;
    const row = {
      round,
      budget: currentBudget,
      selectedTasks: Array.from(selected),
      droppedTasks: Array.from(dropped),
      totalSelected: totalSelectedHours,
      highPrioritySelected: highSel,
      totalHighPriority: highTot,
      decisions: decisionCount,
      revisions: revisionCount,
    };
    const planningEfficiency = highTot > 0 ? highSel / highTot : 0;
    const overcommitRate = totalSelectedHours / currentBudget;
    const selectedLow = tasks.filter((t) => t.priority === "low" && selected.has(t.id)).length;
    const tradeoffQuality = highSel + selectedLow > 0 ? highSel / (highSel + selectedLow) : 0;

    const nextRoundData = [...roundData, row];
    const nextAgg = {
      planning_efficiency: [...agg.planning_efficiency, planningEfficiency],
      overcommit_rate: [...agg.overcommit_rate, overcommitRate],
      tradeoff_quality: [...agg.tradeoff_quality, tradeoffQuality],
    };

    if (round >= maxRounds) {
      const totalDecisions = nextRoundData.reduce((s, x) => s + x.decisions, 0);
      const totalRevisions = nextRoundData.reduce((s, x) => s + x.revisions, 0);
      const avgPlanning =
        nextAgg.planning_efficiency.reduce((a, b) => a + b, 0) / nextAgg.planning_efficiency.length;
      const avgOver = nextAgg.overcommit_rate.reduce((a, b) => a + b, 0) / nextAgg.overcommit_rate.length;
      const avgTrade = nextAgg.tradeoff_quality.reduce((a, b) => a + b, 0) / nextAgg.tradeoff_quality.length;
      const decisiveness = totalDecisions > 0 ? 1 - totalRevisions / totalDecisions : 0;
      const availableHoursPerWeek = budgets.reduce((a, b) => a + b, 0) / budgets.length;
      const avgTaskHours =
        nextRoundData.reduce((sum, r) => {
          const n = r.selectedTasks.length;
          return sum + (n > 0 ? r.totalSelected / n : 0);
        }, 0) / nextRoundData.length;
      const preferredSessionLength = Math.max(1, Math.min(4, avgTaskHours));

      onRunStateChange?.(false);
      onComplete({
        accuracy: avgPlanning,
        mean_response_time: 1000,
        response_time_variance: 100,
        performance_decay: 0,
        retry_depth: 1 - avgPlanning,
        dropout_depth_index: 1 - avgOver,
        recovery_slope: decisiveness,
        raw: {
          total_rounds: maxRounds,
          planning_efficiency: avgPlanning,
          overcommit_rate: avgOver,
          tradeoff_quality: avgTrade,
          decisiveness,
          available_hours_per_week: availableHoursPerWeek,
          preferred_session_length: preferredSessionLength,
          round_data: nextRoundData,
          total_decisions: totalDecisions,
          total_revisions: totalRevisions,
          budget_progression: budgets,
          session_level: sessionLevel,
        },
      });
      setPhase("done");
      return;
    }

    setRoundData(nextRoundData);
    setAgg(nextAgg);
    setRound((r) => r + 1);
    setDecisionCount(0);
    setRevisionCount(0);
    generateTasks();
    showToast(`Round ${round + 1} — budget ${budgets[round]} hours`);
  };

  if (phase === "intro") {
    return (
      <BrutalCard accent="muted" className="assessment-task-intro">
        <h3 className="headline">Time budget builder</h3>
        <p>
          Select tasks that fit your weekly budget. Higher rounds use tighter budgets; later rounds may add an
          emergency task.
        </p>
        <BrutalButton variant="primary" onClick={start} data-testid="task-start">
          Start planning
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

  return (
    <BrutalCard accent="white" className="assessment-time-budget">
      {toast && (
        <div
          style={{
            position: "fixed",
            top: 16,
            right: 16,
            zIndex: 20,
            padding: "10px 16px",
            background: "var(--accent-yellow, #ffeb3b)",
            border: "2px solid #000",
            maxWidth: 360,
            fontSize: 13,
          }}
        >
          {toast}
        </div>
      )}
      {disruptionAlert && (
        <div
          style={{
            position: "fixed",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            zIndex: 30,
            padding: "16px 24px",
            background: "#ff9800",
            color: "#111",
            border: "3px solid #000",
            fontWeight: 700,
          }}
        >
          <div>Disruption</div>
          <div style={{ fontWeight: 500 }}>New task: {disruptionAlert}</div>
        </div>
      )}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, justifyContent: "space-between", marginBottom: 12 }}>
        <span>
          Budget: <strong>{currentBudget}h</strong>
        </span>
        <span>
          Round <strong>{round}</strong> / {maxRounds}
        </span>
        <span>
          Selected: <strong>{totalSelectedHours}h</strong>
        </span>
      </div>
      <div style={{ display: "flex", flexDirection: "row", flexWrap: "wrap", gap: 12 }}>
        <div style={{ flex: "1 1 280px", maxHeight: 420, overflowY: "auto" }}>
          <p className="small-copy" style={{ marginTop: 0 }}>
            Available tasks
          </p>
          {tasks.map((t) => {
            const isSel = selected.has(t.id);
            const isDrop = dropped.has(t.id);
            return (
              <button
                type="button"
                key={t.id}
                onClick={() => toggleTask(t.id)}
                style={{
                  width: "100%",
                  textAlign: "left",
                  padding: 12,
                  marginBottom: 8,
                  borderRadius: 8,
                  border: `2px solid ${isSel ? "#2e7d32" : isDrop ? "#c62828" : "rgba(0,0,0,0.15)"}`,
                  background: isSel ? "rgba(46,125,50,0.12)" : "#fff",
                  opacity: isDrop ? 0.75 : 1,
                  cursor: "pointer",
                }}
              >
                <span style={{ float: "right", fontSize: 11, fontWeight: 700 }}>{t.priority.toUpperCase()}</span>
                <div style={{ fontWeight: 700 }}>{t.name}</div>
                <div className="small-copy">{t.description}</div>
                <div className="small-copy">{t.hours} hours</div>
                {t.isDisruption && (
                  <div className="small-copy" style={{ color: "#e65100" }}>
                    Emergency task
                  </div>
                )}
              </button>
            );
          })}
        </div>
        <div style={{ flex: "0 0 260px" }}>
          <div style={{ border: "2px solid rgba(0,0,0,0.12)", borderRadius: 8, padding: 12, marginBottom: 12 }}>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>Breakdown</div>
            <div className="small-copy">High: {breakdown.high}h</div>
            <div className="small-copy">Medium: {breakdown.medium}h</div>
            <div className="small-copy">Low: {breakdown.low}h</div>
            <div style={{ marginTop: 8, fontWeight: 700 }}>Total: {totalSelectedHours}h</div>
            <div className="small-copy" style={{ color: remaining < 0 ? "#c62828" : undefined }}>
              Remaining: {remaining}h
            </div>
          </div>
          <BrutalButton variant="primary" style={{ width: "100%", marginBottom: 8 }} onClick={confirmSelection}>
            Confirm selection
          </BrutalButton>
          <BrutalButton style={{ width: "100%", marginBottom: 8 }} onClick={clearSelection}>
            Clear all
          </BrutalButton>
          <BrutalButton style={{ width: "100%" }} onClick={autoOptimize}>
            Auto optimize
          </BrutalButton>
          <div className="small-copy" style={{ marginTop: 12 }}>
            <div>Tasks: {tasks.length}</div>
            <div>Selected count: {selected.size}</div>
            <div>High-priority coverage: {efficiencyPct}%</div>
          </div>
        </div>
      </div>
    </BrutalCard>
  );
};
