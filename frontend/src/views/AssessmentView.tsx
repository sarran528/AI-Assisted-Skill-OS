import { Heart } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AssessmentLevelTask, mapTaskResultsToSubmission } from "../components/assessment";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { MetricBar } from "../components/brutal/MetricBar";
import { useCompleteAssessment, useStartAssessment, useSubmitLevel } from "../hooks/useAssessment";

interface LevelState {
  completed: boolean;
  accuracyRecord: boolean[];
  responseTimings: number[];
}

const QUESTION_COUNT = 10;
const LEVELS = [1, 2, 3, 4, 5, 6];
const LEVEL_TIME_SECONDS = 900;

const LEVEL_TITLES: Record<number, string> = {
  1: "Go / No-Go inhibition",
  2: "Flanker attention control",
  3: "Pattern switch survival",
  4: "Rapid tap motor baseline",
  5: "Countdown adaptive challenge",
  6: "Time budget planning",
};

function computeLevelMetrics(levelState: LevelState) {
  const timings = levelState.responseTimings;
  const mean = timings.length > 0 ? timings.reduce((a, b) => a + b, 0) / timings.length : 0;
  const variance =
    timings.length > 0
      ? timings.map((t) => (t - mean) ** 2).reduce((a, b) => a + b, 0) / timings.length
      : 0;

  const firstHalf = levelState.accuracyRecord.slice(0, 5);
  const secondHalf = levelState.accuracyRecord.slice(5, 10);
  const firstAcc = firstHalf.length > 0 ? firstHalf.filter(Boolean).length / firstHalf.length : 0;
  const secondAcc = secondHalf.length > 0 ? secondHalf.filter(Boolean).length / secondHalf.length : 0;

  return {
    accuracy: levelState.accuracyRecord.filter(Boolean).length / Math.max(1, levelState.accuracyRecord.length),
    mean_response_time: mean,
    response_time_variance: variance,
    performance_decay: Math.max(0, firstAcc - secondAcc),
  };
}

function formatTimer(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

const ABANDON_METRICS = {
  accuracy: 0,
  mean_response_time: 0,
  response_time_variance: 0,
  performance_decay: 0,
  retry_depth: 1,
  dropout_depth_index: 1,
  recovery_slope: 0,
  raw: {},
};

export function AssessmentView() {
  const navigate = useNavigate();

  const [currentLevel, setCurrentLevel] = useState(1);
  const [livesRemaining, setLivesRemaining] = useState(3);
  const [timeLeftSeconds, setTimeLeftSeconds] = useState(LEVEL_TIME_SECONDS);
  const [sessionId, setSessionId] = useState<string>("assessment-session-local");
  const [lifeLossFlash, setLifeLossFlash] = useState(false);
  const [taskRunning, setTaskRunning] = useState(false);

  const [levels, setLevels] = useState<Record<number, LevelState>>(() =>
    Object.fromEntries(
      LEVELS.map((level) => [
        level,
        {
          completed: false,
          accuracyRecord: [],
          responseTimings: [],
        },
      ])
    ) as Record<number, LevelState>
  );

  const startMutation = useStartAssessment();
  const submitLevelMutation = useSubmitLevel();
  const completeMutation = useCompleteAssessment();

  useEffect(() => {
    startMutation.mutate(undefined, {
      onSuccess: (data) => {
        setSessionId(data.session_id || "assessment-session-local");
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (levels[currentLevel].completed) {
      return;
    }
    if (!taskRunning) {
      return;
    }
    const timer = window.setInterval(() => {
      setTimeLeftSeconds((value) => Math.max(0, value - 1));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [taskRunning, currentLevel, levels]);

  useEffect(() => {
    if (timeLeftSeconds > 0 || levels[currentLevel].completed || !taskRunning) {
      return;
    }

    setLifeLossFlash(true);
    window.setTimeout(() => setLifeLossFlash(false), 450);

    setLivesRemaining((value) => {
      const next = Math.max(0, value - 1);
      if (next === 0) {
        window.setTimeout(() => handleAbandonLevel(currentLevel), 0);
      }
      return next;
    });

    setTimeLeftSeconds(LEVEL_TIME_SECONDS);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeLeftSeconds, currentLevel, levels, taskRunning]);

  const completedLevels = useMemo(
    () => Object.entries(levels).filter(([, state]) => state.completed).map(([level]) => Number(level)),
    [levels]
  );

  function selectLevel(level: number) {
    setCurrentLevel(level);
    setTimeLeftSeconds(LEVEL_TIME_SECONDS);
    setLivesRemaining(3);
    setTaskRunning(false);
  }

  function submitPayloadForLevel(level: number, taskMetrics: Record<string, unknown>) {
    submitLevelMutation.mutate(mapTaskResultsToSubmission(sessionId, level, taskMetrics));
  }

  function handleTaskComplete(level: number, taskMetrics: Record<string, unknown>) {
    submitPayloadForLevel(level, taskMetrics);
    setLevels((previous) => ({
      ...previous,
      [level]: {
        ...previous[level],
        completed: true,
      },
    }));
    setTaskRunning(false);
    setTimeLeftSeconds(LEVEL_TIME_SECONDS);
    setLivesRemaining(3);
  }

  function handleAbandonLevel(level: number) {
    submitPayloadForLevel(level, ABANDON_METRICS);
    setLevels((previous) => ({
      ...previous,
      [level]: {
        ...previous[level],
        completed: true,
      },
    }));
    setTaskRunning(false);
    setTimeLeftSeconds(LEVEL_TIME_SECONDS);
    setLivesRemaining(3);
  }

  function handleQuickComplete() {
    LEVELS.forEach((level) => {
      if (!levels[level].completed) {
        const generated: LevelState = {
          completed: true,
          accuracyRecord: Array.from({ length: QUESTION_COUNT }, (_, index) => index % 2 === 0),
          responseTimings: Array.from({ length: QUESTION_COUNT }, () => 1200),
        };

        const metrics = computeLevelMetrics(generated);
        submitLevelMutation.mutate(
          mapTaskResultsToSubmission(sessionId, level, {
            accuracy: metrics.accuracy,
            mean_response_time: metrics.mean_response_time,
            response_time_variance: metrics.response_time_variance,
            performance_decay: metrics.performance_decay,
            retry_depth: 0.1,
            dropout_depth_index: 0.1,
            recovery_slope: 0.9,
            raw: {
              available_hours_per_week: 8,
              preferred_session_length: 45,
            },
          })
        );
      }
    });

    setLevels(
      Object.fromEntries(
        LEVELS.map((level) => [
          level,
          {
            completed: true,
            accuracyRecord: Array.from({ length: QUESTION_COUNT }, (_, index) => index % 2 === 0),
            responseTimings: Array.from({ length: QUESTION_COUNT }, () => 1200),
          },
        ])
      ) as Record<number, LevelState>
    );
    setTaskRunning(false);
  }

  function handleCompleteAssessment() {
    completeMutation.mutate(
      {
        session_id: sessionId,
        completed_levels: completedLevels,
      },
      {
        onSuccess: () => navigate("/dashboard"),
      }
    );
  }

  const active = levels[currentLevel];
  const levelTitle = LEVEL_TITLES[currentLevel] ?? `Level ${currentLevel}`;

  return (
    <main className="assessment-page" data-testid="assessment-screen">
      <header className="top-bar">
        <strong>SKILLOS</strong>
        <span data-testid="assessment-session-id">Session: {sessionId}</span>
        <span>Level {currentLevel}/6</span>
        <span className={`hearts-row ${lifeLossFlash ? "life-loss-flash" : ""}`.trim()} data-testid="lives-left">
          {[0, 1, 2].map((heart) => (
            <Heart key={heart} size={16} fill={heart < livesRemaining ? "currentColor" : "transparent"} />
          ))}
        </span>
        <span data-testid="timer">{formatTimer(timeLeftSeconds)}</span>
      </header>

      <section className="level-grid">
        {LEVELS.map((level) => {
          const isCompleted = levels[level].completed;
          const isActive = level === currentLevel;
          const status = isCompleted ? "COMPLETED" : isActive ? "IN PROGRESS" : "AVAILABLE";

          return (
            <button
              key={level}
              type="button"
              data-testid={`level-card-${level}`}
              className={`level-card ${isActive ? "level-card--active" : ""}`.trim()}
              onClick={() => selectLevel(level)}
              disabled={isCompleted}
            >
              Level {level}
              <span className="small-copy">{status}</span>
            </button>
          );
        })}
      </section>

      <BrutalCard accent="yellow" className="assessment-headline-card">
        <h1 className="headline">Executive control assessment</h1>
        <p>{levelTitle}</p>
      </BrutalCard>

      <section className="assessment-content">
        <BrutalCard className="question-card">
          {active.completed ? (
            <>
              <h2>Level {currentLevel} complete</h2>
              <p className="small-copy">Pick another level above, or finish the session when all six are done.</p>
            </>
          ) : (
            <>
              <h2 data-testid="assessment-task-heading">{levelTitle}</h2>
              <p className="small-copy">
                Timer runs only while a task is in progress ({formatTimer(LEVEL_TIME_SECONDS)} budget per attempt).
              </p>
              <div className="assessment-task-mount">
                <AssessmentLevelTask
                  key={`${currentLevel}-${sessionId}`}
                  level={currentLevel}
                  onRunStateChange={setTaskRunning}
                  onComplete={(metrics) => handleTaskComplete(currentLevel, metrics)}
                />
              </div>
            </>
          )}
        </BrutalCard>

        <BrutalCard className="metrics-card">
          <h2 className="section-title">Session progress</h2>
          <MetricBar label="Levels completed" value={completedLevels.length / 6} />
          <MetricBar
            label="Current level status"
            value={active.completed ? 1 : taskRunning ? 0.5 : 0}
          />
          <MetricBar label="Lives remaining" value={livesRemaining / 3} />
        </BrutalCard>
      </section>

      <section className="button-row">
        <BrutalButton data-testid="quick-complete-assessment" onClick={handleQuickComplete}>
          Quick complete 6 levels
        </BrutalButton>
        <BrutalButton
          data-testid="complete-assessment"
          variant="primary"
          onClick={handleCompleteAssessment}
          disabled={completedLevels.length < 6}
        >
          Complete assessment
        </BrutalButton>
      </section>
    </main>
  );
}
