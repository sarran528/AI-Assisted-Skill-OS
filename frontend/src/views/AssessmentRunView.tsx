import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { useNavigationStore } from "../store/navigationStore";

const TOTAL_QUESTIONS = 10;
const LEVEL_NAMES: Record<number, string> = {
  1: "Executive Control",
  2: "Sustained Attention",
  3: "Working Memory",
  4: "Motor Baseline",
  5: "Stress Resilience",
  6: "Time Constraint",
};

const choices = ["A", "B", "C", "D"];

export function AssessmentRunView() {
  const navigate = useNavigate();
  const { level } = useParams();
  const levelNumber = Number(level ?? "");
  const isValidLevel = Number.isInteger(levelNumber) && levelNumber >= 1 && levelNumber <= 6;
  const {
    assessmentProgress,
    updateAssessmentLevel,
    setProfileState,
    setSystemState,
  } = useNavigationStore();
  const initializedRef = useRef(false);

  const [question, setQuestion] = useState(1);
  const [lives, setLives] = useState(() => (isValidLevel ? assessmentProgress[levelNumber]?.livesRemaining ?? 3 : 3));
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    if (!isValidLevel || initializedRef.current) {
      return;
    }
    initializedRef.current = true;
    const attempts = assessmentProgress[levelNumber]?.attempts ?? 0;
    updateAssessmentLevel(levelNumber, {
      status: "in_progress",
      attempts: attempts + 1,
      livesRemaining: 3,
      questionsAnswered: 0,
    });
    setLives(3);
  }, [assessmentProgress, isValidLevel, levelNumber, updateAssessmentLevel]);

  const timerSeconds = useMemo(() => Math.max(0, 60 - question * 2), [question]);

  const finishLevel = (completed: boolean) => {
    if (!isValidLevel) {
      navigate("/assessment");
      return;
    }
    updateAssessmentLevel(levelNumber, {
      status: completed ? "complete" : "failed",
      completedAt: completed ? new Date().toISOString() : undefined,
      questionsAnswered: completed ? TOTAL_QUESTIONS : question - 1,
      livesRemaining: completed ? lives : 0,
    });

    const levelsAfter = { ...assessmentProgress, [levelNumber]: { ...assessmentProgress[levelNumber], status: completed ? "complete" : "failed" } };
    const completedCount = Object.values(levelsAfter).filter((item) => item.status === "complete").length;
    if (completedCount === 6) {
      setProfileState({
        isActive: true,
        dimensions: {
          cognitive_capacity: 0.74,
          attention_stability: 0.61,
          learning_tolerance: 0.58,
          motor_baseline: 0.69,
          stress_resilience: 0.72,
          time_constraint: 0.45,
        },
      });
      setSystemState("profile_active");
    }
    navigate("/assessment");
  };

  const onAnswer = (choice: string) => {
    const correct = choices[(question + levelNumber) % choices.length];
    if (choice !== correct) {
      const nextLives = lives - 1;
      setLives(nextLives);
      if (isValidLevel) {
        updateAssessmentLevel(levelNumber, { livesRemaining: nextLives });
      }
      setFeedback(`Life lost. "${choice}" was incorrect.`);
      if (nextLives <= 0) {
        window.setTimeout(() => finishLevel(false), 500);
      }
      return;
    }

    const nextQuestion = question + 1;
    setFeedback("Correct.");
    if (isValidLevel) {
      updateAssessmentLevel(levelNumber, { questionsAnswered: question, livesRemaining: lives });
    }
    if (nextQuestion > TOTAL_QUESTIONS) {
      window.setTimeout(() => finishLevel(true), 250);
      return;
    }
    setQuestion(nextQuestion);
  };

  if (!isValidLevel) {
    return (
      <main className="assessment-page">
        <BrutalCard accent="red">
          <h1 className="headline">Assessment Level Not Found</h1>
          <p className="small-copy">This assessment route is invalid. Go back to continue from the assessment progress card.</p>
          <BrutalButton variant="secondary" onClick={() => navigate("/assessment")}>
            Back to Assessment
          </BrutalButton>
        </BrutalCard>
      </main>
    );
  }

  return (
    <main style={{ minHeight: "100vh", padding: "2rem", background: "#fffef0" }}>
      <h1 className="headline">{LEVEL_NAMES[levelNumber] ?? `Level ${levelNumber}`}</h1>
      <p>Question {question} / {TOTAL_QUESTIONS}</p>
      <p>Lives remaining: {[0, 1, 2].map((i) => (i < lives ? "●" : "○")).join(" ")}</p>
      <p>Timer: {timerSeconds}s</p>
      <div className="brutal-card" style={{ marginTop: "1rem" }}>
        <p>Choose the best answer for this cognitive prompt.</p>
        <div className="button-row">
          {choices.map((choice) => (
            <BrutalButton key={choice} onClick={() => onAnswer(choice)}>
              {choice}
            </BrutalButton>
          ))}
        </div>
        {feedback ? <p className="small-copy" style={{ marginTop: "1rem" }}>{feedback}</p> : null}
      </div>
    </main>
  );
}
