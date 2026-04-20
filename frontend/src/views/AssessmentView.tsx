import { Heart } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

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

export function AssessmentView() {
  const navigate = useNavigate();

  const [currentLevel, setCurrentLevel] = useState(1);
  const [currentQuestion, setCurrentQuestion] = useState(1);
  const [livesRemaining, setLivesRemaining] = useState(3);
  const [timeLeftSeconds, setTimeLeftSeconds] = useState(900);
  const [questionStartTs, setQuestionStartTs] = useState<number>(Date.now());
  const [sessionId, setSessionId] = useState<string>("assessment-session-local");

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
    // Intentionally run once at mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setTimeLeftSeconds((value) => Math.max(0, value - 1));
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (timeLeftSeconds === 0 && !levels[currentLevel].completed) {
      handleLevelComplete();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeLeftSeconds]);

  const completedLevels = useMemo(
    () => Object.entries(levels).filter(([, state]) => state.completed).map(([level]) => Number(level)),
    [levels]
  );

  function handleAnswerSubmission(isCorrect: boolean) {
    const now = Date.now();
    const responseTime = now - questionStartTs;

    setLevels((previous) => {
      const levelState = previous[currentLevel];
      const nextLevelState: LevelState = {
        ...levelState,
        accuracyRecord: [...levelState.accuracyRecord, isCorrect],
        responseTimings: [...levelState.responseTimings, responseTime],
      };
      return {
        ...previous,
        [currentLevel]: nextLevelState,
      };
    });

    if (!isCorrect) {
      setLivesRemaining((value) => Math.max(0, value - 1));
    }

    if (currentQuestion >= QUESTION_COUNT) {
      handleLevelComplete();
      return;
    }

    setCurrentQuestion((value) => value + 1);
    setQuestionStartTs(Date.now());
  }

  function handleLevelComplete(level = currentLevel) {
    const levelState = levels[level];
    const metrics = computeLevelMetrics(levelState);

    submitLevelMutation.mutate({
      level,
      metrics: {
        accuracy: Math.round(metrics.accuracy * 100),
        expected_time: Math.max(1, metrics.mean_response_time / 1000),
        latency_stability: Math.min(25, metrics.response_time_variance / 10000),
        decay_inverse: Math.max(0, 1 - metrics.performance_decay),
        dropout: Math.max(0, 3 - livesRemaining),
        retry: 0,
        recovery: 1,
      },
      time_constraint: {
        available_hours_per_week: 8,
        preferred_session_length: 45,
      },
    });

    setLevels((previous) => ({
      ...previous,
      [level]: {
        ...previous[level],
        completed: true,
      },
    }));

    const nextLevel = LEVELS.find((candidate) => !levels[candidate].completed && candidate !== level);
    if (nextLevel) {
      setCurrentLevel(nextLevel);
    }
    setCurrentQuestion(1);
    setLivesRemaining(3);
    setQuestionStartTs(Date.now());
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
        submitLevelMutation.mutate({
          level,
          metrics: {
            accuracy: Math.round(metrics.accuracy * 100),
            expected_time: 2,
            latency_stability: 4,
            decay_inverse: Math.max(0, 1 - metrics.performance_decay),
            dropout: 0,
            retry: 0,
            recovery: 1,
          },
          time_constraint: {
            available_hours_per_week: 8,
            preferred_session_length: 45,
          },
        });
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

  return (
    <main className="assessment-page">
      <header className="top-bar">
        <strong>SKILLOS</strong>
        <span>Level {currentLevel}/6</span>
        <span className="hearts-row">
          {[0, 1, 2].map((heart) => (
            <Heart key={heart} size={16} fill={heart < livesRemaining ? "currentColor" : "transparent"} />
          ))}
        </span>
        <span>
          {Math.floor(timeLeftSeconds / 60)}:{String(timeLeftSeconds % 60).padStart(2, "0")}
        </span>
      </header>

      <section className="level-grid">
        {LEVELS.map((level) => {
          const isCompleted = levels[level].completed;
          return (
            <button
              key={level}
              type="button"
              data-testid={`level-card-${level}`}
              className={`level-card ${level === currentLevel ? "level-card--active" : ""}`}
              onClick={() => {
                setCurrentLevel(level);
                setCurrentQuestion(1);
                setQuestionStartTs(Date.now());
              }}
            >
              Level {level} {isCompleted ? "✓" : ""}
            </button>
          );
        })}
      </section>

      <BrutalCard accent="yellow" className="assessment-headline-card">
        <h1 className="headline">Executive Control Assessment</h1>
        <p>Working memory + inhibition</p>
      </BrutalCard>

      <section className="assessment-content">
        <BrutalCard className="question-card">
          <h2>
            Question {currentQuestion} / {QUESTION_COUNT}
          </h2>
          <p>Respond to the active cognitive prompt.</p>
          <div className="button-row">
            <BrutalButton data-testid="submit-response" variant="primary" onClick={() => handleAnswerSubmission(true)}>
              Submit Response
            </BrutalButton>
            <BrutalButton onClick={() => handleAnswerSubmission(false)} variant="danger">
              Mark Incorrect
            </BrutalButton>
          </div>
        </BrutalCard>

        <BrutalCard className="metrics-card">
          <h2 className="section-title">Performance</h2>
          <MetricBar label="Accuracy" value={levels[currentLevel].accuracyRecord.filter(Boolean).length / Math.max(1, levels[currentLevel].accuracyRecord.length)} />
          <MetricBar label="Latency" value={0.4} />
          <MetricBar label="Retry" value={0} />
        </BrutalCard>
      </section>

      <section className="button-row">
        <BrutalButton data-testid="quick-complete-assessment" onClick={handleQuickComplete}>
          Quick Complete 6 Levels
        </BrutalButton>
        <BrutalButton
          data-testid="complete-assessment"
          variant="primary"
          onClick={handleCompleteAssessment}
          disabled={completedLevels.length < 6}
        >
          Complete Assessment
        </BrutalButton>
      </section>
    </main>
  );
}
