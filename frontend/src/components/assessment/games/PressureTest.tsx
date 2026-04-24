import React, { useState, useEffect, useRef, useCallback } from 'react';
import { NeoBrutalistLayout } from '../NeoBrutalistLayout';
import { GameRulesOverlay } from '../GameRulesOverlay';
import { BehavioralSignals } from '../../../stores/assessmentStore';

interface Rule {
  label: string;
  check: (n: number, presses: number) => boolean;
}

const RULES: Rule[] = [
  { label: 'PRESS WHEN EVEN', check: (n, p) => (n % 2 === 0 ? p === 1 : p === 0) },
  { label: 'PRESS WHEN ODD', check: (n, p) => (n % 2 !== 0 ? p === 1 : p === 0) },
  { label: 'PRESS WHEN > 50', check: (n, p) => (n > 50 ? p === 1 : p === 0) },
  { label: 'PRESS WHEN < 30', check: (n, p) => (n < 30 ? p === 1 : p === 0) },
  { label: 'DO NOT PRESS', check: (_n, p) => p === 0 },
  { label: 'PRESS EXACTLY 3 TIMES', check: (_n, p) => p === 3 },
  { label: 'MULTIPLES OF 5 ONLY', check: (n, p) => (n % 5 === 0 ? p === 1 : p === 0) },
  { label: 'NUMBER ENDS IN 7', check: (n, p) => (n % 10 === 7 ? p === 1 : p === 0) },
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
  const [currentNumber, setCurrentNumber] = useState(0);
  const [timeLeft, setTimeLeft] = useState(8000);

  // Use refs for values that timers/callbacks need to read without stale closures
  const pressesRef = useRef(0);
  const livesRef = useRef(3);
  const roundRef = useRef(1);
  const scoreRef = useRef(0);
  const ruleRef = useRef<Rule>(RULES[0]);
  const numberRef = useRef(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const results = useRef<boolean[]>([]);
  const lifeLossRounds = useRef<number[]>([]);
  const usedRuleIndices = useRef<number[]>([]);

  const [pressDisplay, setPressDisplay] = useState(0);

  // Keep refs in sync
  useEffect(() => { livesRef.current = lives; }, [lives]);
  useEffect(() => { roundRef.current = round; }, [round]);
  useEffect(() => { scoreRef.current = score; }, [score]);

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

  const getTimeWindow = (r: number) => (r <= 3 ? 8000 : r <= 6 ? 6000 : 4000);

  const beginRound = useCallback(() => {
    clearTimer();
    const rule = pickRandomRule();
    const num = Math.floor(Math.random() * 100);

    setCurrentRule(rule);
    ruleRef.current = rule;
    setCurrentNumber(num);
    numberRef.current = num;
    pressesRef.current = 0;
    setPressDisplay(0);
    setPhase('showRule');

    // Show rule for 1.5s, then start the active phase
    setTimeout(() => {
      const tw = getTimeWindow(roundRef.current);
      setTimeLeft(tw);
      setPhase('active');

      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 100) {
            evaluateRound();
            return 0;
          }
          return prev - 100;
        });
      }, 100);
    }, 1500);
  }, []);

  const startPlaying = () => {
    setPhase('showRule');
    beginRound();
  };

  // Start first round when entering playing state
  useEffect(() => {
    return () => clearTimer();
  }, []);

  const handlePress = () => {
    if (phase !== 'active') return;
    pressesRef.current += 1;
    setPressDisplay(pressesRef.current);
  };

  const evaluateRound = () => {
    clearTimer();

    const isCorrect = ruleRef.current.check(numberRef.current, pressesRef.current);
    results.current.push(isCorrect);

    if (isCorrect) {
      const tw = getTimeWindow(roundRef.current);
      let points = 30;
      // Bonus if answered with < 2s remaining on the clock
      // We can't easily read timeLeft here due to stale closure, so skip bonus for simplicity
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

    // Brief pause to show result, then move on
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

    const firstThreeAcc = results.current.slice(0, 3).filter(r => r).length / 3;
    const lastFourAcc = results.current.slice(6).filter(r => r).length / Math.max(1, results.current.slice(6).length);
    const performance_decay = Math.max(0, firstThreeAcc - lastFourAcc);

    let recoverySuccess = 0;
    let recoveryAttempts = 0;
    lifeLossRounds.current.forEach(r => {
      const nextIdx = r; // 1-indexed round → 0-indexed next result
      if (nextIdx < results.current.length) {
        recoveryAttempts++;
        if (results.current[nextIdx]) recoverySuccess++;
      }
    });
    const recovery_slope = recoveryAttempts > 0 ? recoverySuccess / recoveryAttempts : 1;

    const signals: BehavioralSignals = {
      accuracy,
      mean_response_time: 0,
      response_time_variance: 0,
      performance_decay,
      retry_depth: 0,
      dropout_depth_index: 0,
      recovery_slope,
    };

    onComplete(signals, score, lives);
  };

  if (phase === 'rules') {
    return (
      <GameRulesOverlay
        title="PRESSURE TEST"
        tag="STRESS RESILIENCE"
        rules={[
          'A RULE AND A NUMBER WILL APPEAR ON SCREEN',
          'THE RULE FLASHES FOR 1.5 SECONDS — MEMORIZE IT',
          'THEN THE TIMER STARTS — FOLLOW THE RULE',
          'E.G.: RULE IS "PRESS WHEN EVEN", NUMBER IS 42 → PRESS ONCE',
          'RULE IS "DO NOT PRESS" → DON\'T PRESS AT ALL',
          'RULE IS "PRESS EXACTLY 3 TIMES" → PRESS 3 TIMES',
          'TIMER GETS SHORTER AS ROUNDS PROGRESS',
        ]}
        onStart={startPlaying}
      />
    );
  }

  const lastResult = results.current.length > 0 ? results.current[results.current.length - 1] : null;

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

            <div style={{ fontSize: '120px', fontWeight: 900, marginBottom: '48px' }}>
              {currentNumber}
            </div>

            <button
              className="neo-brutalist-button neo-brutalist-button--primary"
              style={{ fontSize: '28px', padding: '28px 64px' }}
              onClick={handlePress}
            >
              [ PRESS ]
            </button>

            <div style={{ marginTop: '24px', fontSize: '18px', fontWeight: 900 }}>
              PRESSES THIS ROUND: {pressDisplay}
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
              RULE: {currentRule.label} | NUMBER: {currentNumber} | PRESSES: {pressDisplay}
            </p>
          </div>
        )}
      </div>
    </NeoBrutalistLayout>
  );
};
