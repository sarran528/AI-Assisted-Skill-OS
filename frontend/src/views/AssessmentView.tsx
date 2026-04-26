import { useNavigate } from "react-router-dom";
import { BrutalButton } from "../components/brutal/BrutalButton";
import { BrutalCard } from "../components/brutal/BrutalCard";
import { useNavigationStore } from "../store/navigationStore";
import { useAssessmentStore, GAME_IDS } from "../stores/assessmentStore";
import { useStartAssessment, useCompleteAssessment, useAssessmentStatus } from "../hooks/useAssessment";
import { useEffect } from "react";

const LEVELS = [
  { id: 1, name: "Stroop Test", tag: "Executive Control", description: "Measures inhibition and impulse control." },
  { id: 2, name: "Flanker Test", tag: "Sustained Attention", description: "Tracks focus consistency over repeated tasks." },
  { id: 3, name: "Puzzle Game", tag: "Working Memory", description: "Measures temporary information retention." },
  { id: 4, name: "Dart Game", tag: "Motor Baseline", description: "Checks motor speed and rhythm stability." },
  { id: 5, name: "Pressure Test", tag: "Stress Resilience", description: "Evaluates stability under pressure." },
  { id: 6, name: "Time Questions", tag: "Time Constraint", description: "Measures decision quality under time limits." },
];

export function AssessmentView() {
  const navigate = useNavigate();
  const { games, sessionId, setSessionId } = useAssessmentStore();
  const { setProfileState, setSystemState } = useNavigationStore();

  const startMutation = useStartAssessment();
  const completeMutation = useCompleteAssessment();
  const { data: statusData, isLoading: statusLoading } = useAssessmentStatus();

  useEffect(() => {
    if (statusLoading) return;
    
    if (statusData?.session_id && statusData?.status === "in_progress") {
      if (sessionId !== statusData.session_id) {
        setSessionId(statusData.session_id);
      }
    } else if (!sessionId && !startMutation.isPending && !startMutation.isError) {
      startMutation.mutate(undefined, {
        onSuccess: (data) => {
          if (data && 'session_id' in data) {
            setSessionId(data.session_id as string);
          }
        }
      });
    }
  }, [sessionId, statusData, statusLoading, startMutation, setSessionId]);

  const completedCount = Array.isArray(statusData?.levels_completed)
    ? statusData.levels_completed.length
    : GAME_IDS.filter((id) => games[id].completed).length;
  const localSubmittedCount = GAME_IDS.filter((id) => games[id].completed).length;
  const backendReadyToCompute =
    (statusData?.status === "in_progress" || statusData?.status === "completed") &&
    Array.isArray(statusData?.levels_completed) &&
    statusData.levels_completed.length === 6;
    
  const canComputeProfile = Boolean(
    sessionId && backendReadyToCompute
  );

  const getStatusBadge = (attempts: number) => {
    if (attempts === 0) return { label: "NOT ATTEMPTED", class: "neo-brutalist-status-badge--grey" };
    if (attempts === 1) return { label: "TRIED ONCE", class: "neo-brutalist-status-badge--yellow" };
    if (attempts === 2) return { label: "TRIED TWICE", class: "neo-brutalist-status-badge--orange" };
    if (attempts === 3) return { label: "TRIED THRICE", class: "neo-brutalist-status-badge--green" };
    return { label: `TRIED ${attempts} TIMES`, class: "neo-brutalist-status-badge--green" };
  };

  const handleComputeProfile = () => {
    if (!sessionId) return;

    completeMutation.mutate({
      session_id: sessionId,
    }, {
      onSuccess: (data: any) => {
        setProfileState({
          isActive: true,
          dimensions: {
            cognitive_capacity: data.cognitive_capacity,
            attention_stability: data.attention_stability,
            learning_tolerance: data.learning_tolerance,
            motor_baseline: data.motor_baseline,
            stress_resilience: data.stress_resilience,
            time_constraint: data.time_constraint,
          },
          learning_parameters: data.learning_parameters || null,
        });
        setSystemState("profile_active");
        navigate("/dashboard");
      }
    });
  };

  return (
    <main className="neo-brutalist" style={{ padding: "2rem", minHeight: "100vh" }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 className="neo-brutalist-title">ASSESSMENT SUITE</h1>
        <button
          className="neo-brutalist-button neo-brutalist-button--primary"
          onClick={handleComputeProfile}
          disabled={!canComputeProfile || completeMutation.isPending}
          title={!canComputeProfile ? "Submit all 6 levels first" : undefined}
          style={!canComputeProfile ? { opacity: 0.6, cursor: "not-allowed" } : undefined}
        >
          {completeMutation.isPending ? "COMPUTING..." : "COMPUTE ASSESSMENT"}
        </button>
      </div>

      <div className="neo-brutalist-card" style={{ marginBottom: "2rem" }}>
        <h2>PROGRESS: {completedCount} / 6 LEVELS</h2>
        <div className="metric-row__bar" style={{ height: '30px', marginTop: '1rem' }}>
          <div className="metric-row__fill" style={{ width: `${(completedCount / 6) * 100}%`, background: '#FFE500' }} />
        </div>
      </div>

      <div className="skill-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '2rem' }}>
        {LEVELS.map((level) => {
          const game = games[level.id as keyof typeof games];
          const badge = getStatusBadge(game.attempts);

          return (
            <div key={level.id} className="neo-brutalist-card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div className="neo-brutalist-tag" style={{ alignSelf: 'flex-start' }}>{level.tag}</div>
              <h3 style={{ margin: 0, fontSize: '20px' }}>{level.name}</h3>
              <p className="small-copy" style={{ flex: 1 }}>{level.description}</p>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '12px' }}>
                <span className={`neo-brutalist-status-badge ${badge.class}`}>
                  {badge.label}
                </span>
                <div style={{ fontSize: '18px' }}>
                  {Array.from({ length: 3 }).map((_, i) => (
                    <span key={i}>{i < game.lastLivesRemaining ? '●' : '○'}</span>
                  ))}
                </div>
              </div>
              
              <div style={{ fontWeight: '900', marginTop: '8px' }}>
                BEST: {game.bestScore} PTS
              </div>

              <button 
                className="neo-brutalist-button neo-brutalist-button--primary"
                style={{ marginTop: '16px', width: '100%' }}
                onClick={() => navigate(`/assessment/run/${level.id}`)}
              >
                {game.attempts > 0 ? 'RETRY ASSESSMENT' : 'START ASSESSMENT'}
              </button>
            </div>
          );
        })}
      </div>
    </main>
  );
}
