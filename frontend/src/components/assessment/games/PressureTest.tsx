import React, { useState, useEffect, useRef } from 'react';
import { NeoBrutalistLayout } from '../NeoBrutalistLayout';
import { GameRulesOverlay } from '../GameRulesOverlay';
import { BehavioralSignals } from '../../../stores/assessmentStore';

interface Rule {
  label: string;
  check: (n: number, presses: number) => boolean;
  expectedPresses: (n: number) => number;
}

const digitSum = (n: number) =>
  Math.min(String(n).split('').reduce((a, d) => a + parseInt(d), 0), 9);

const RULES: Rule[] = [
  // --- COUNT-BASED (majority) ---
  {
    label: 'PRESS THE NUMBER OF DIGITS',
    check: (n, p) => p === String(n).length,
    expectedPresses: (n) => String(n).length,
  },
  {
    label: 'PRESS SUM OF DIGITS (MAX 9)',
    check: (n, p) => p === digitSum(n),
    expectedPresses: (n) => digitSum(n),
  },
  {
    label: 'PRESS THE TENS DIGIT',
    check: (n, p) => p === Math.floor(n / 10),
    expectedPresses: (n) => Math.floor(n / 10),
  },
  {
    label: 'PRESS THE UNITS DIGIT',
    check: (n, p) => p === (n % 10),
    expectedPresses: (n) => n % 10,
  },
  {
    label: 'PRESS NUMBER OF EVEN DIGITS',
    check: (n, p) => {
      const count = String(n).split('').filter(d => parseInt(d) % 2 === 0).length;
      return p === count;
    },
    expectedPresses: (n) => String(n).split('').filter(d => parseInt(d) % 2 === 0).length,
  },
  {
    label: 'PRESS NUMBER OF ODD DIGITS',
    check: (n, p) => {
      const count = String(n).split('').filter(d => parseInt(d) % 2 !== 0).length;
      return p === count;
    },
    expectedPresses: (n) => String(n).split('').filter(d => parseInt(d) % 2 !== 0).length,
  },
  {
    label: 'PRESS DIGITS THAT ARE > 4',
    check: (n, p) => {
      const count = String(n).split('').filter(d => parseInt(d) > 4).length;
      return p === count;
    },
    expectedPresses: (n) => String(n).split('').filter(d => parseInt(d) > 4).length,
  },
  {
    label: 'PRESS LARGEST DIGIT',
    check: (n, p) => p === Math.max(...String(n).split('').map(Number)),
    expectedPresses: (n) => Math.max(...String(n).split('').map(Number)),
  },
  {
    label: 'PRESS SMALLEST DIGIT',
    check: (n, p) => p === Math.min(...String(n).split('').map(Number)),
    expectedPresses: (n) => Math.min(...String(n).split('').map(Number)),
  },
  {
    label: 'PRESS DIGIT COUNT × 2',
    check: (n, p) => p === String(n).length * 2,
    expectedPresses: (n) => String(n).length * 2,
  },
  // --- CONDITIONAL (minority) ---
  {
    label: 'DO NOT PRESS',
    check: (_n, p) => p === 0,
    expectedPresses: () => 0,
  },
  {
    label: 'PRESS IF NUMBER IS PRIME',
    check: (n, p) => {
      const isPrime = n > 1 && Array.from({ length: Math.floor(Math.sqrt(n)) }, (_, i) => i + 2).every(i => n % i !== 0);
      return isPrime ? p === 1 : p === 0;
    },
    expectedPresses: (n) => {
      const isPrime = n > 1 && Array.from({ length: Math.floor(Math.sqrt(n)) }, (_, i) => i + 2).every(i => n % i !== 0);
      return isPrime ? 1 : 0;
    },
  },
];

interface PressureTestProps {
  onComplete: (signals: BehavioralSignals, score: number, livesRemaining: number) => void;
  onFail: () => void;
}

export const PressureTest: React.FC<PressureTestProps> = ({ onComplete, onFail }) => {
  const [phase, setPhase] = useState<'rules' | 'showRule' | 'active' | 'roundResult'>('rules');
  const [round, setRound] = useState(1);
  const [lives, setLives] = useState(3);
  const [score, setScore] = useState(0);
  const [currentRule, setCurrentRule] = useState<Rule>(RULES[0]);
  const [currentNumber, setCurrentNumber] = useState(10);
  const [timeLeft, setTimeLeft] = useState(8000);

  // Refs for timer-critical state
  const pressesRef = useRef(0);
  const livesRef = useRef(3);
  const roundRef = useRef(1);
  const ruleRef = useRef<Rule>(RULES[0]);
  const numberRef = useRef(10);
  const timeLeftRef = useRef(8000);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const evaluatingRef = useRef(false);

  // Signal collection refs
  const results = useRef<boolean[]>([]);
  const lifeLossRounds = useRef<number[]>([]);
  const usedRuleIndices = useRef<number[]>([]);

  // Press timestamp tracking
  const roundStartTimeRef = useRef<number>(0);
  const pressTimestampsRef = useRef<number[]>([]);
  const allPressTimestamps = useRef<number[]>([]);

  // Per-round tracking for retry_depth and dropout
  const perRoundPresses = useRef<number[]>([]);
  const perRoundExpected = useRef<number[]>([]);

  const [pressDisplay, setPressDisplay] = useState(0);

  useEffect(() => { livesRef.current = lives; }, [lives]);
  useEffect(() => { roundRef.current = round; }, [round]);

  const clearTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const pickRandomRule = (): Rule => {
    const unused = RULES.map((_, i) => i).filter(i => !usedRuleIndices.current.includes(i));
    const pool = unused.length > 0 ? unused : RULES.map((_, i) => i);
    if (unused.length === 0) usedRuleIndices.current = [];
    const idx = pool[Math.floor(Math.random() * pool.length)];
    usedRuleIndices.current.push(idx);
    return RULES[idx];
  };

  // 8s for round 1, decreasing by 0.2s each round (8.0 → 6.2)
  const getTimeWindow = (r: number) => 8000 - (r - 1) * 200;

  const beginRound = () => {
    clearTimer();
    evaluatingRef.current = false;
    const rule = pickRandomRule();
    const num = Math.floor(Math.random() * 90) + 10; // always 2-digit: 10–99

    setCurrentRule(rule);
    ruleRef.current = rule;
    setCurrentNumber(num);
    numberRef.current = num;
    pressesRef.current = 0;
    pressTimestampsRef.current = [];
    setPressDisplay(0);
    setPhase('showRule');

    setTimeout(() => {
      const tw = getTimeWindow(roundRef.current);
      setTimeLeft(tw);
      timeLeftRef.current = tw;
      roundStartTimeRef.current = performance.now();
      setPhase('active');

      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 0) return 0;
          const next = prev <= 100 ? 0 : prev - 100;
          timeLeftRef.current = next;
          if (next === 0) {
            evaluateRound();
          }
          return next;
        });
      }, 100);
    }, 1500);
  };

  const startPlaying = () => {
    setPhase('showRule');
    beginRound();
  };

  useEffect(() => {
    return () => clearTimer();
  }, []);

  const handlePress = () => {
    if (phase !== 'active') return;
    pressesRef.current += 1;
    setPressDisplay(pressesRef.current);
    pressTimestampsRef.current.push(performance.now() - roundStartTimeRef.current);
  };

  const evaluateRound = () => {
    if (evaluatingRef.current) return;
    evaluatingRef.current = true;
    clearTimer();

    const isCorrect = ruleRef.current.check(numberRef.current, pressesRef.current);
    results.current.push(isCorrect);

    allPressTimestamps.current.push(...pressTimestampsRef.current);
    perRoundPresses.current.push(pressesRef.current);
    perRoundExpected.current.push(ruleRef.current.expectedPresses(numberRef.current));

    if (isCorrect) {
      let points = 30;
      if (timeLeftRef.current < 2000) points += 20;
      setScore(prev => prev + points);
    } else {
      lifeLossRounds.current.push(roundRef.current);
      const nextLives = livesRef.current - 1;
      setLives(nextLives);
      if (nextLives <= 0) {
        setTimeout(onFail, 500);
        return;
      }
    }

    setPhase('roundResult');

    setTimeout(() => {
      if (roundRef.current >= 10) {
        finishGame();
      } else {
        setRound(prev => prev + 1);
        beginRound();
      }
    }, 800);
  };

  const finishGame = () => {
    const accuracy = results.current.filter(r => r).length / results.current.length;

    const rts = allPressTimestamps.current;
    let mean_response_time = 0;
    let response_time_variance = 0;
    if (rts.length > 0) {
      mean_response_time = rts.reduce((a, b) => a + b, 0) / rts.length;
      response_time_variance = rts.reduce((acc, t) => acc + Math.pow(t - mean_response_time, 2), 0) / rts.length;
    }

    const firstThreeAcc = results.current.slice(0, 3).filter(r => r).length / 3;
    const lastFourAcc = results.current.slice(6).filter(r => r).length / Math.max(1, results.current.slice(6).length);
    const performance_decay = Math.max(0, firstThreeAcc - lastFourAcc);

    let totalExcess = 0;
    for (let i = 0; i < perRoundPresses.current.length; i++) {
      totalExcess += Math.max(0, perRoundPresses.current[i] - perRoundExpected.current[i]);
    }

    let dropoutIdx = -1;
    for (let i = 0; i < perRoundPresses.current.length; i++) {
      if (perRoundExpected.current[i] > 0 && perRoundPresses.current[i] === 0) {
        dropoutIdx = i;
        break;
      }
    }

    let recoverySuccess = 0;
    let recoveryAttempts = 0;
    lifeLossRounds.current.forEach(r => {
      const nextIdx = r;
      if (nextIdx < results.current.length) {
        recoveryAttempts++;
        if (results.current[nextIdx]) recoverySuccess++;
      }
    });

    const signals: BehavioralSignals = {
      accuracy,
      mean_response_time,
      response_time_variance,
      performance_decay,
      retry_depth: totalExcess,
      dropout_depth_index: dropoutIdx === -1 ? 1 : dropoutIdx / results.current.length,
      recovery_slope: recoveryAttempts > 0 ? recoverySuccess / recoveryAttempts : 1,
    };

    onComplete(signals, score, lives);
  };

  if (phase === 'rules') {
    return (
      <GameRulesOverlay
        title="PRESSURE TEST"
        tag="STRESS RESILIENCE"
        rules={[
          'A RULE AND A 2-DIGIT NUMBER WILL APPEAR ON SCREEN',
          'THE RULE TELLS YOU HOW MANY TIMES TO PRESS THE BUTTON',
          'E.G.: "PRESS THE TENS DIGIT" + NUMBER 73 → PRESS 7 TIMES',
          'E.G.: "PRESS SUM OF DIGITS" + NUMBER 45 → 4+5 = PRESS 9 TIMES',
          '"DO NOT PRESS" MEANS PRESS ZERO TIMES',
          'TIMER STARTS AT 8S AND GETS 0.2S SHORTER EACH ROUND',
          'MATCH THE EXACT TARGET COUNT TO SCORE',
        ]}
        onStart={startPlaying}
      />
    );
  }

  const lastResult = results.current.length > 0 ? results.current[results.current.length - 1] : null;
  const targetPresses = currentRule.expectedPresses(currentNumber);

  return (
    <NeoBrutalistLayout
      title="PRESSURE TEST"
      tag="STRESS RESILIENCE"
      lives={lives}
      currentQuestion={round}
      totalQuestions={10}
      score={score}
    >
      <div
        className="neo-brutalist-card"
        style={{
          textAlign: 'center',
          padding: '64px',
          minHeight: '400px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}
      >
        {phase === 'showRule' && (
          <div>
            <h2 style={{ fontSize: '24px', color: '#FF2D2D', marginBottom: '16px' }}>
              ROUND {round} — NEW RULE:
            </h2>
            <div style={{ fontSize: '40px', fontWeight: 900 }}>{currentRule.label}</div>
            <p style={{ marginTop: '16px', fontSize: '14px' }}>MEMORIZE THIS RULE...</p>
          </div>
        )}

        {phase === 'active' && (
          <>
            <div
              style={{
                marginBottom: '24px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div
                style={{
                  background: '#FFE500',
                  padding: '8px 16px',
                  border: '2px solid #0a0a0a',
                  fontWeight: 900,
                  fontSize: '16px',
                }}
              >
                {currentRule.label}
              </div>
              <div style={{ fontSize: '20px', fontWeight: 900 }}>
                {(timeLeft / 1000).toFixed(1)}S
              </div>
            </div>

            <div style={{ fontSize: '120px', fontWeight: 900, marginBottom: '16px' }}>
              {currentNumber}
            </div>

            <button
              className="neo-brutalist-button neo-brutalist-button--primary"
              style={{ fontSize: '28px', padding: '28px 64px', marginBottom: '24px' }}
              onClick={handlePress}
            >
              [ PRESS ]
            </button>

            <div style={{ fontSize: '18px', fontWeight: 900 }}>
              PRESSES: {pressDisplay}
            </div>
          </>
        )}

        {phase === 'roundResult' && (
          <div>
            <div
              style={{
                fontSize: '48px',
                fontWeight: 900,
                color: lastResult ? '#00C851' : '#FF2D2D',
              }}
            >
              {lastResult ? '✓ CORRECT' : '✗ WRONG'}
            </div>
            <p style={{ marginTop: '16px', fontSize: '16px' }}>
              RULE: {currentRule.label} | NUMBER: {currentNumber} | YOUR PRESSES: {pressDisplay} | TARGET: {targetPresses}
            </p>
          </div>
        )}
      </div>
    </NeoBrutalistLayout>
  );
};
