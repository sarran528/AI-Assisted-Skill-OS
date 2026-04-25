import { useNavigate, useParams } from "react-router-dom";
import { useAssessmentStore, GameId, BehavioralSignals, TimeSignals } from "../stores/assessmentStore";
import { StroopTest } from "../components/assessment/games/StroopTest";
import { FlankerTest } from "../components/assessment/games/FlankerTest";
import { PuzzleGame } from "../components/assessment/games/PuzzleGame";
import { DartGame } from "../components/assessment/games/DartGame";
import { PressureTest } from "../components/assessment/games/PressureTest";
import { TimeQuestions } from "../components/assessment/games/TimeQuestions";

export function AssessmentRunView() {
  const { level } = useParams();
  const navigate = useNavigate();
  const finishLevel = useAssessmentStore((state) => state.finishLevel);
  
  const levelNumber = Number(level) as GameId;

  const handleComplete = (signals: BehavioralSignals, score: number, livesRemaining: number, timeSignals?: TimeSignals) => {
    finishLevel(levelNumber, signals, timeSignals, livesRemaining, score, true);
    navigate("/assessment");
  };

  const handleFail = () => {
    const emptySignals: BehavioralSignals = {
      accuracy: 0,
      mean_response_time: 0,
      response_time_variance: 0,
      performance_decay: 0,
      retry_depth: 0,
      dropout_depth_index: 0,
      recovery_slope: 0
    };
    finishLevel(levelNumber, emptySignals, undefined, 0, 0, false);
    navigate("/assessment");
  };

  const renderGame = () => {
    switch (levelNumber) {
      case 1:
        return <StroopTest onComplete={handleComplete} onFail={handleFail} />;
      case 2:
        return <FlankerTest onComplete={handleComplete} onFail={handleFail} />;
      case 3:
        return <PuzzleGame onComplete={handleComplete} onFail={handleFail} />;
      case 4:
        return <DartGame onComplete={handleComplete} onFail={handleFail} />;
      case 5:
        return <PressureTest onComplete={handleComplete} onFail={handleFail} />;
      case 6:
        return <TimeQuestions onComplete={handleComplete} onFail={handleFail} />;
      default:
        return (
          <div className="neo-brutalist-card" style={{ padding: '32px', textAlign: 'center' }}>
            <h1 className="neo-brutalist-title">LEVEL NOT FOUND</h1>
            <p style={{ marginTop: '16px' }}>This assessment level does not exist.</p>
            <button 
              className="neo-brutalist-button neo-brutalist-button--primary"
              style={{ marginTop: '24px' }}
              onClick={() => navigate("/assessment")}
            >
              BACK TO ASSESSMENT
            </button>
          </div>
        );
    }
  };

  return (
    <main style={{ minHeight: "100vh", background: "#f5f0e8" }}>
      {renderGame()}
    </main>
  );
}
