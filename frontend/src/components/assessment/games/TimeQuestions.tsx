import React, { useState } from 'react';
import { NeoBrutalistLayout } from '../NeoBrutalistLayout';
import { GameRulesOverlay } from '../GameRulesOverlay';
import { BehavioralSignals, TimeSignals } from '../../../stores/assessmentStore';
import { detectContradiction } from '../../../utils/contradictionDetection';

interface TimeQuestionsProps {
  onComplete: (signals: BehavioralSignals, score: number, livesRemaining: number, timeSignals: TimeSignals) => void;
  onFail: () => void;
}

const QUESTIONS = [
  {
    q: "How many hours per week can you dedicate to practice?",
    opts: ['Less than 2 hours', '2 to 5 hours', '5 to 10 hours', '10 or more hours'],
  },
  {
    q: "What is your ideal single session length?",
    opts: ['15 minutes', '30 minutes', '45 minutes', '60 minutes or more'],
  },
  {
    q: "How many days per week can you practice?",
    opts: ['1–2 days', '3–4 days', '5–6 days', 'Every day'],
  },
  {
    q: "If a session runs over, what do you do?",
    opts: ['Stop immediately', 'Finish current task', 'Push through', 'Skip next session'],
  },
  {
    q: "How do you handle a missed practice day?",
    opts: ['Double next session', 'Catch up gradually', 'Accept and move on', 'Always miss more after'],
  },
  {
    q: "Realistically, how often do unexpected events cut your practice?",
    opts: ['Rarely', 'Sometimes', 'Often', 'Almost always'],
  },
];

export const TimeQuestions: React.FC<TimeQuestionsProps> = ({ onComplete, onFail }) => {
  const [gameState, setGameState] = useState<'rules' | 'playing'>('rules');
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [lives, setLives] = useState(3);
  const [score, setScore] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  const [contradictionMsg, setContradictionMsg] = useState('');

  const handleAnswer = (optIdx: number) => {
    const newAnswers = [...answers, optIdx];
    
    // Check for contradiction
    if (newAnswers.length >= 3) {
      const isContradiction = detectContradiction(newAnswers);
      if (isContradiction) {
        handleContradiction();
        return;
      }
    }

    setAnswers(newAnswers);
    setScore(prev => prev + 30);

    if (index >= 5) {
      finish(newAnswers);
    } else {
      setIndex(prev => prev + 1);
      setRetryCount(0); // Reset retry count for new question
    }
  };

  const handleContradiction = () => {
    const nextLives = lives - 1;
    setLives(nextLives);
    
    if (nextLives <= 0) {
      onFail();
    } else {
      setContradictionMsg('LOGICAL CONTRADICTION DETECTED. LIFE LOST. RE-ANSWER THIS QUESTION.');
      setTimeout(() => setContradictionMsg(''), 2500);
      if (retryCount === 0) {
        setRetryCount(1);
      } else {
        setIndex(Math.max(0, index - 1));
        setAnswers(prev => prev.slice(0, -1));
        setRetryCount(0);
      }
    }
  };

  const finish = (finalAnswers: number[]) => {
    // available_hours_per_week: derived from Q1 (hrs)
    const hrsMap = [1, 3.5, 7.5, 12];
    const available_hours_per_week = hrsMap[finalAnswers[0]];

    // preferred_session_length: Q2 (mins)
    const sessionMap = [15, 30, 45, 60];
    const preferred_session_length = sessionMap[finalAnswers[1]];

    // schedule_reliability: derived from Q4+Q5+Q6 (0-1 scale)
    // Lower values for risky options (Skip session, Always miss more after, Almost always)
    const reliabilityScore = (
      (3 - finalAnswers[3]) + // Skip session = 0, Stop immediately = 3
      (2 - (finalAnswers[4] === 3 ? 2 : 0)) + // Always miss more = 0
      (3 - finalAnswers[5]) // Rarely = 3, Almost always = 0
    ) / 8;

    const timeSignals: TimeSignals = {
      available_hours_per_week,
      preferred_session_length,
      schedule_reliability: Math.max(0, Math.min(1, reliabilityScore)),
      flex_buffer: (3 - finalAnswers[5]) * 0.33, // estimation
    };

    const signals: BehavioralSignals = {
      accuracy: 1.0,
      mean_response_time: 0,
      response_time_variance: 0,
      performance_decay: 0,
      retry_depth: 0,
      dropout_depth_index: 0,
      recovery_slope: 0
    };

    const livesBonus = lives * 20;
    const finalScore = score + livesBonus;
    onComplete(signals, finalScore, lives, timeSignals);
  };

  if (gameState === 'rules') {
    return (
      <GameRulesOverlay
        title="TIME QUESTIONS"
        tag="TIME CONSTRAINT"
        rules={[
          "YOU WILL BE ASKED 6 QUESTIONS ABOUT YOUR WEEKLY AVAILABILITY",
          "ANSWER EACH QUESTION AS HONESTLY AS POSSIBLE",
          "THE SYSTEM WILL CHECK YOUR ANSWERS FOR LOGICAL CONSISTENCY",
          "IF YOUR ANSWERS CONTRADICT EACH OTHER, YOU LOSE A LIFE",
          "EXAMPLE: '< 2HRS/WEEK' AND 'EVERY DAY 60MIN SESSIONS' IS A CONTRADICTION"
        ]}
        onStart={() => setGameState('playing')}
      />
    );
  }

  const currentQ = QUESTIONS[index];

  return (
    <NeoBrutalistLayout
      title="TIME QUESTIONS"
      tag="TIME CONSTRAINT"
      lives={lives}
      currentQuestion={index + 1}
      totalQuestions={6}
      score={score}
    >
      <div className="neo-brutalist-card" style={{ maxWidth: '800px', margin: '0 auto' }}>
        {contradictionMsg && (
          <div style={{ background: '#FF2D2D', color: '#f5f0e8', padding: '16px', marginBottom: '24px', border: '3px solid #0a0a0a', fontWeight: 900, fontSize: '16px' }}>
            ⚠ {contradictionMsg}
          </div>
        )}
        <h2 style={{ fontSize: '28px', marginBottom: '48px', lineHeight: 1.4 }}>{currentQ.q}</h2>
        
        <div style={{ display: 'grid', gap: '16px' }}>
          {currentQ.opts.map((opt, i) => (
            <button
              key={i}
              className="neo-brutalist-button"
              style={{ textAlign: 'left', justifyContent: 'flex-start', fontSize: '18px' }}
              onClick={() => handleAnswer(i)}
            >
              {i + 1}. {opt}
            </button>
          ))}
        </div>
      </div>
    </NeoBrutalistLayout>
  );
};
