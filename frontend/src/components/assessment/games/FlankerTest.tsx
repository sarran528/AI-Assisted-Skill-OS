import React, { useState, useEffect, useRef } from 'react';
import { NeoBrutalistLayout } from '../NeoBrutalistLayout';
import { GameRulesOverlay } from '../GameRulesOverlay';
import { BehavioralSignals } from '../../../stores/assessmentStore';

interface FlankerTestProps {
  onComplete: (signals: BehavioralSignals, score: number, livesRemaining: number) => void;
  onFail: () => void;
}

export const FlankerTest: React.FC<FlankerTestProps> = ({ onComplete, onFail }) => {
  const [gameState, setGameState] = useState<'rules' | 'playing'>('rules');
  const [question, setQuestion] = useState(1);
  const [lives, setLives] = useState(3);
  const [score, setScore] = useState(0);
  const [currentArrows, setCurrentArrows] = useState<string[]>([]);
  const [centerDir, setCenterDir] = useState<'L' | 'R'>('L');
  const [timeLeft, setTimeLeft] = useState(3000);
  const [isGameOver, setIsGameOver] = useState(false);

  const responseTimes = useRef<number[]>([]);
  const results = useRef<boolean[]>([]);
  const startTime = useRef<number>(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const generateQ = () => {
    const dirs: ('L' | 'R')[] = ['L', 'R'];
    const center = dirs[Math.floor(Math.random() * 2)];
    setCenterDir(center);

    let flankers: string[] = [];
    const difficulty = question <= 4 ? 'congruent' : question <= 7 ? 'mixed' : 'incongruent';

    if (difficulty === 'congruent') {
      flankers = [center, center, center, center, center];
    } else if (difficulty === 'incongruent') {
      const opp = center === 'L' ? 'R' : 'L';
      flankers = [opp, opp, center, opp, opp];
    } else {
      flankers = Array.from({ length: 5 }, (_, i) => (i === 2 ? center : dirs[Math.floor(Math.random() * 2)]));
    }

    setCurrentArrows(flankers);
    
    // Timer reduces from 3s to 1.5s
    const window = 3000 - (question - 1) * 166; 
    setTimeLeft(window);
    startTime.current = Date.now();
  };

  useEffect(() => {
    if (gameState !== 'playing') return;
    generateQ();
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [gameState]);

  useEffect(() => {
    if (isGameOver || gameState !== 'playing') return;
    if (timerRef.current) clearInterval(timerRef.current);
    
    timerRef.current = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 100) {
          handleAnswer(null); // Timeout
          return 0;
        }
        return prev - 100;
      });
    }, 100);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [question, isGameOver]);

  const handleAnswer = (dir: 'L' | 'R' | null) => {
    if (timerRef.current) clearInterval(timerRef.current);
    const rt = Date.now() - startTime.current;

    if (dir === centerDir) {
      results.current.push(true);
      responseTimes.current.push(rt);
      setScore(prev => prev + 25);
    } else {
      results.current.push(false);
      const nextLives = lives - 1;
      setLives(nextLives);
      if (nextLives <= 0) {
        setIsGameOver(true);
        setTimeout(onFail, 1000);
        return;
      }
    }

    if (question >= 10) {
      finish();
    } else {
      setQuestion(prev => prev + 1);
      generateQ();
    }
  };

  const finish = () => {
    const accuracy = results.current.filter(r => r).length / 10;
    const mean_rt = responseTimes.current.length > 0 
      ? responseTimes.current.reduce((a, b) => a + b, 0) / responseTimes.current.length 
      : 0;
    
    const variance = responseTimes.current.length > 0
      ? responseTimes.current.reduce((a, b) => a + Math.pow(b - mean_rt, 2), 0) / responseTimes.current.length
      : 0;

    const firstHalfErr = results.current.slice(0, 5).filter(r => !r).length;
    const secondHalfErr = results.current.slice(5).filter(r => !r).length;
    const performance_decay = Math.max(0, (secondHalfErr - firstHalfErr) / 5);

    const firstErrIdx = results.current.indexOf(false);
    const dropout_depth_index = firstErrIdx === -1 ? 1 : firstErrIdx / 10;

    const signals: BehavioralSignals = {
      accuracy,
      mean_response_time: mean_rt,
      response_time_variance: variance,
      performance_decay,
      retry_depth: 0,
      dropout_depth_index,
      recovery_slope: 0
    };

    const livesBonus = lives * 50;
    const finalScore = score + livesBonus;
    onComplete(signals, finalScore, lives);
  };

  if (gameState === 'rules') {
    return (
      <GameRulesOverlay
        title="FLANKER TEST"
        tag="SUSTAINED ATTENTION"
        rules={[
          "A ROW OF 5 ARROWS WILL APPEAR ON SCREEN",
          "IDENTIFY WHICH DIRECTION THE CENTER ARROW IS POINTING",
          "IGNORE THE SURROUNDING ARROWS — THEY ARE DISTRACTORS",
          "THE CENTER ARROW IS SHOWN IN BLUE FOR CLARITY",
          "ANSWER SPEED MATTERS — THE TIMER SHRINKS EACH QUESTION"
        ]}
        onStart={() => setGameState('playing')}
      />
    );
  }

  return (
    <NeoBrutalistLayout
      title="FLANKER TEST"
      tag="SUSTAINED ATTENTION"
      lives={lives}
      currentQuestion={question}
      totalQuestions={10}
      score={score}
    >
      <div className="neo-brutalist-card" style={{ textAlign: 'center', padding: '64px' }}>
        <div style={{ marginBottom: '32px', fontSize: '18px' }}>
          TIMER: {(timeLeft / 1000).toFixed(1)}S
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginBottom: '64px' }}>
          {currentArrows.map((dir, i) => (
            <div 
              key={i} 
              style={{ 
                fontSize: i === 2 ? '120px' : '80px', 
                fontWeight: 900,
                color: i === 2 ? '#0057FF' : '#0a0a0a',
                transition: 'all 0.1s ease'
              }}
            >
              {dir === 'L' ? '←' : '→'}
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '32px', justifyContent: 'center' }}>
          <button
            className="neo-brutalist-button"
            style={{ fontSize: '32px', padding: '24px 48px' }}
            onClick={() => handleAnswer('L')}
            disabled={isGameOver}
          >
            [ ← LEFT ]
          </button>
          <button
            className="neo-brutalist-button"
            style={{ fontSize: '32px', padding: '24px 48px' }}
            onClick={() => handleAnswer('R')}
            disabled={isGameOver}
          >
            [ RIGHT → ]
          </button>
        </div>
        
        <p style={{ marginTop: '32px' }}>IDENTIFY THE CENTER ARROW DIRECTION ONLY</p>
      </div>
    </NeoBrutalistLayout>
  );
};
