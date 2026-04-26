import React, { useState, useEffect, useRef } from 'react';
import { NeoBrutalistLayout } from '../NeoBrutalistLayout';
import { GameRulesOverlay } from '../GameRulesOverlay';
import { BehavioralSignals } from '../../../stores/assessmentStore';

const WORDS = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'PURPLE'];
const COLORS = ['#FF2D2D', '#0057FF', '#00C851', '#FFE500', '#9B5DE5'];

interface StroopTestProps {
  onComplete: (signals: BehavioralSignals, score: number, livesRemaining: number) => void;
  onFail: () => void;
}

export const StroopTest: React.FC<StroopTestProps> = ({ onComplete, onFail }) => {
  const [gameState, setGameState] = useState<'rules' | 'playing'>('rules');
  const [question, setQuestion] = useState(1);
  const [lives, setLives] = useState(3);
  const [score, setScore] = useState(0);
  const [currentQ, setCurrentQ] = useState({ word: '', inkColor: '', correctLabel: '' });
  const [timeLeft, setTimeLeft] = useState(4000);
  const [isGameOver, setIsGameOver] = useState(false);

  const responseTimes = useRef<number[]>([]);
  const results = useRef<boolean[]>([]);
  const startTime = useRef<number>(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const generateQ = () => {
    // Pick a random word
    const wordIdx = Math.floor(Math.random() * WORDS.length);
    // Pick a random color that is DIFFERENT from the word to create interference
    let colorIdx;
    do {
      colorIdx = Math.floor(Math.random() * COLORS.length);
    } while (colorIdx === wordIdx);
    
    setCurrentQ({
      word: WORDS[wordIdx],
      inkColor: COLORS[colorIdx],
      correctLabel: WORDS[colorIdx] // The correct answer is the INK COLOR
    });

    const window = question <= 3 ? 4000 : question <= 6 ? 3000 : 2000;
    setTimeLeft(window);
    startTime.current = Date.now();
  };

  const startPlaying = () => {
    setGameState('playing');
    generateQ();
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  useEffect(() => {
    if (gameState !== 'playing' || isGameOver) return;

    if (timerRef.current) clearInterval(timerRef.current);
    
    timerRef.current = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 100) {
          handleTimeout();
          return 0;
        }
        return prev - 100;
      });
    }, 100);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [question, gameState, isGameOver]);

  const handleTimeout = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    results.current.push(false);
    const nextLives = lives - 1;
    setLives(nextLives);
    if (nextLives <= 0) {
      setIsGameOver(true);
      setTimeout(onFail, 1000);
    } else {
      nextStep();
    }
  };

  const handleAnswer = (label: string) => {
    if (timerRef.current) clearInterval(timerRef.current);
    const rt = Date.now() - startTime.current;
    const window = question <= 3 ? 4000 : question <= 6 ? 3000 : 2000;

    if (label === currentQ.correctLabel) {
      results.current.push(true);
      responseTimes.current.push(rt);
      const points = rt < window / 2 ? 30 : 15;
      setScore(prev => prev + points);
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

    nextStep();
  };

  const nextStep = () => {
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

    const firstHalfAcc = results.current.slice(0, 5).filter(r => r).length / 5;
    const secondHalfAcc = results.current.slice(5).filter(r => r).length / 5;
    const performance_decay = Math.max(0, firstHalfAcc - secondHalfAcc);

    const livesBonus = lives * 50;
    const finalScore = score + livesBonus;

    const signals: BehavioralSignals = {
      accuracy,
      mean_response_time: mean_rt,
      response_time_variance: variance,
      performance_decay,
      retry_depth: 0,
      dropout_depth_index: 0,
      recovery_slope: 0
    };

    onComplete(signals, finalScore, lives);
  };

  if (gameState === 'rules') {
    return (
      <GameRulesOverlay
        title="STROOP TEST"
        tag="EXECUTIVE CONTROL"
        rules={[
          "A COLOR WORD WILL BE SHOWN (E.G., 'RED')",
          "THE WORD WILL BE PRINTED IN A MISMATCHED INK COLOR",
          "YOU MUST IDENTIFY THE INK COLOR, NOT THE WORD TEXT",
          "E.G., IF 'BLUE' IS PRINTED IN GREEN INK, PRESS 'GREEN'",
          "ANSWER QUICKLY TO MAXIMIZE YOUR SCORE"
        ]}
        onStart={startPlaying}
      />
    );
  }

  return (
    <NeoBrutalistLayout
      title="STROOP TEST"
      tag="EXECUTIVE CONTROL"
      lives={lives}
      currentQuestion={question}
      totalQuestions={10}
      score={score}
    >
      <div className="neo-brutalist-card" style={{ textAlign: 'center', padding: '64px' }}>
        <div style={{ marginBottom: '32px', fontSize: '18px' }}>
          TIMER: {(timeLeft / 1000).toFixed(1)}S
        </div>
        
        <div 
          style={{ 
            fontSize: '72px', 
            fontWeight: 900, 
            color: currentQ.inkColor,
            marginBottom: '64px',
            textShadow: '3px 3px 0px #0a0a0a'
          }}
        >
          {currentQ.word}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '600px', margin: '0 auto' }}>
          <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))' }}>
            {WORDS.slice(0, 4).map((label) => (
              <button
                key={label}
                className="neo-brutalist-button neo-brutalist-button--primary"
                onClick={() => handleAnswer(label)}
                disabled={isGameOver}
              >
                {label}
              </button>
            ))}
          </div>
          <button
            key="PURPLE"
            className="neo-brutalist-button neo-brutalist-button--primary"
            onClick={() => handleAnswer("PURPLE")}
            disabled={isGameOver}
          >
            PURPLE
          </button>
        </div>
        
        <p style={{ marginTop: '32px', fontWeight: 900 }}>PRESS THE BUTTON MATCHING THE INK COLOR</p>
      </div>
    </NeoBrutalistLayout>
  );
};