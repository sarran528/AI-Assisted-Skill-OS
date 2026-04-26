import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAssessmentStore, GameId, BehavioralSignals, TimeSignals } from "../stores/assessmentStore";
import { useSubmitLevel, useAssessmentStatus } from "../hooks/useAssessment";
import { StroopTest } from "../components/assessment/games/StroopTest";
import { FlankerTest } from "../components/assessment/games/FlankerTest";
import { PuzzleGame } from "../components/assessment/games/PuzzleGame";
import { DartGame } from "../components/assessment/games/DartGame";
import { PressureTest } from "../components/assessment/games/PressureTest";
import { TimeQuestions } from "../components/assessment/games/TimeQuestions";

export function AssessmentRunView() {
  const { level } = useParams();
  const navigate = useNavigate();
  const { finishLevel, sessionId, setSessionId } = useAssessmentStore();
  const submitMutation = useSubmitLevel();
  
  const [viewState, setViewState] = useState<'playing' | 'summary'>('playing');
  const [summaryData, setSummaryData] = useState<{ signals: BehavioralSignals, score: number, livesRemaining: number, timeSignals?: TimeSignals } | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  
  const levelNumber = Number(level) as GameId;
  const { data: statusData } = useAssessmentStatus();

  useEffect(() => {
    if (statusData?.session_id && sessionId !== statusData.session_id) {
      setSessionId(statusData.session_id);
    }
  }, [statusData, sessionId, setSessionId]);

  const handleComplete = (signals: BehavioralSignals, score: number, livesRemaining: number, timeSignals?: TimeSignals) => {
    setSummaryData({ signals, score, livesRemaining, timeSignals });
    setViewState('summary');
  };

  const handleContinue = () => {
    if (!summaryData) return;
    const { signals, score, livesRemaining, timeSignals } = summaryData;

    setSubmitError(null);

    // Submit to backend first, then mark local completion
    if (sessionId) {
      submitMutation.mutate({
        session_id: sessionId,
        level: levelNumber,
        metrics: {
          accuracy: signals.accuracy,
          expected_time: signals.mean_response_time / 1000,
          latency_stability: signals.response_time_variance / 1000000,
          decay_inverse: Math.max(0, 1 - signals.performance_decay),
          dropout: signals.dropout_depth_index,
          retry: signals.retry_depth,
          recovery: signals.recovery_slope
        },
        time_constraint: {
          available_hours_per_week: timeSignals?.available_hours_per_week || 0,
          preferred_session_length: timeSignals?.preferred_session_length || 0
        },
        score: score,
        lives_remaining: livesRemaining
      }, {
        onSuccess: () => {
          finishLevel(levelNumber, signals, timeSignals, livesRemaining, score, true);
          navigate("/assessment");
        },
        onError: () => {
          setSubmitError("Failed to submit this level. Please try Continue again.");
        }
      });
    } else {
      setSubmitError("No active assessment session found. Please go back and restart assessment.");
    }
  };

  const handleRetry = () => {
    setViewState('playing');
    setSummaryData(null);
    // Note: We don't call finishLevel here, we just restart the UI state
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
    setSummaryData({ signals: emptySignals, score: 0, livesRemaining: 0 });
    setViewState('summary');
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
      {viewState === 'playing' ? (
        renderGame()
      ) : (
        <div className="neo-brutalist-layout" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: '20px' }}>
          <div className="neo-brutalist-card" style={{ padding: '64px', textAlign: 'center', maxWidth: '700px', width: '100%' }}>
            <h1 className="neo-brutalist-title" style={{ fontSize: '48px', marginBottom: '8px' }}>
              {summaryData && summaryData.livesRemaining > 0 ? 'LEVEL COMPLETE' : 'LEVEL FAILED'}
            </h1>
            <p style={{ fontWeight: 900, opacity: 0.7, marginBottom: '32px' }}>
              {summaryData && summaryData.livesRemaining > 0 ? 'METRICS RECORDED SUCCESSFULLY' : 'INSUFFICIENT LIVES REMAINING'}
            </p>
            
            <div style={{ 
              fontSize: '84px', 
              fontWeight: 900, 
              margin: '32px 0', 
              color: '#00C851',
              textShadow: '4px 4px 0px #0a0a0a'
            }}>
              SCORE: {summaryData?.score}
            </div>

            <div style={{ 
              marginBottom: '48px', 
              padding: '24px', 
              background: '#FFE500', 
              border: '4px solid #0a0a0a', 
              fontWeight: 900,
              boxShadow: '8px 8px 0px #0a0a0a',
              textAlign: 'left'
            }}>
              <div style={{ fontSize: '20px', marginBottom: '8px' }}>⚠️ ATTENTION REQUIRED</div>
              <p style={{ fontSize: '16px' }}>
                Retrying this level will reset your current score, but it will **increase your attempt count** in your cognitive profile. 
                Higher attempts generally indicate lower learning efficiency.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '24px', justifyContent: 'center' }}>
              <button 
                className="neo-brutalist-button neo-brutalist-button--primary"
                style={{ padding: '24px 48px', fontSize: '24px', flex: 1 }}
                onClick={handleContinue}
                disabled={submitMutation.isPending}
              >
                {submitMutation.isPending ? 'SAVING...' : 'CONTINUE'}
              </button>
              <button 
                className="neo-brutalist-button"
                style={{ 
                  padding: '24px 48px', 
                  fontSize: '24px', 
                  background: '#0a0a0a', 
                  color: 'white',
                  flex: 1
                }}
                onClick={handleRetry}
              >
                RETRY
              </button>
            </div>
            {submitError ? (
              <p style={{ marginTop: "20px", color: "#D32F2F", fontWeight: 900 }}>
                {submitError}
              </p>
            ) : null}
          </div>
        </div>
      )}
    </main>
  );
}
