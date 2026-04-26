import React, { useState, useEffect, useRef } from 'react';
import { NeoBrutalistLayout } from '../NeoBrutalistLayout';
import { GameRulesOverlay } from '../GameRulesOverlay';
import { BehavioralSignals } from '../../../stores/assessmentStore';

interface DartGameProps {
  onComplete: (signals: BehavioralSignals, score: number, livesRemaining: number) => void;
  onFail: () => void;
}

// 5 levels with escalating speeds
const LEVEL_SPEEDS = [0.8, 1.4, 2.2, 3.2, 3.8];
const TOTAL_DART_LEVELS = 5;
const BOARD_SIZE = 400; // px
const TARGET_RADIUS = 24; // px — bullseye

export const DartGame: React.FC<DartGameProps> = ({ onComplete, onFail }) => {
  const [gameState, setGameState] = useState<'rules' | 'yAxis' | 'xAxis' | 'result'>('rules');
  const [level, setLevel] = useState(1);
  const [lives, setLives] = useState(3);
  const [score, setScore] = useState(0);
  const [yLocked, setYLocked] = useState<number | null>(null);
  const [xLocked, setXLocked] = useState<number | null>(null);
  const [chancesLeft, setChancesLeft] = useState(4);
  const [thrownDarts, setThrownDarts] = useState<Array<{ x: number; y: number; hit: boolean }>>([]);

  const yPosRef = useRef(0.5); // 0–1, normalized
  const xPosRef = useRef(0.5);
  const yDirRef = useRef(1);
  const xDirRef = useRef(1);
  const frameRef = useRef<number>();
  const lastTimeRef = useRef<number>();
  const [yDisplay, setYDisplay] = useState(0.5);
  const [xDisplay, setXDisplay] = useState(0.5);

  const hits = useRef(0);
  const totalShots = useRef(0);
  const precisionScores = useRef<number[]>([]);

  const speed = LEVEL_SPEEDS[Math.min(level - 1, LEVEL_SPEEDS.length - 1)];

  const animateY = (time: number) => {
    if (lastTimeRef.current !== undefined) {
      const dt = (time - lastTimeRef.current) / 1000;
      let next = yPosRef.current + yDirRef.current * speed * dt;
      if (next >= 1) { next = 1; yDirRef.current = -1; }
      if (next <= 0) { next = 0; yDirRef.current = 1; }
      yPosRef.current = next;
      setYDisplay(next);
    }
    lastTimeRef.current = time;
    frameRef.current = requestAnimationFrame(animateY);
  };

  const animateX = (time: number) => {
    if (lastTimeRef.current !== undefined) {
      const dt = (time - lastTimeRef.current) / 1000;
      let next = xPosRef.current + xDirRef.current * speed * dt;
      if (next >= 1) { next = 1; xDirRef.current = -1; }
      if (next <= 0) { next = 0; xDirRef.current = 1; }
      xPosRef.current = next;
      setXDisplay(next);
    }
    lastTimeRef.current = time;
    frameRef.current = requestAnimationFrame(animateX);
  };

  useEffect(() => {
    if (gameState === 'yAxis') {
      lastTimeRef.current = undefined;
      yPosRef.current = 0.5;
      yDirRef.current = 1;
      frameRef.current = requestAnimationFrame(animateY);
    } else if (gameState === 'xAxis') {
      lastTimeRef.current = undefined;
      xPosRef.current = 0.5;
      xDirRef.current = 1;
      frameRef.current = requestAnimationFrame(animateX);
    }
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [gameState, level]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        e.preventDefault();
        handleThrow();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [gameState, yLocked]);

  const handleThrow = () => {
    if (gameState === 'yAxis') {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      setYLocked(yPosRef.current);
      setGameState('xAxis');
      lastTimeRef.current = undefined;
    } else if (gameState === 'xAxis') {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      const finalX = xPosRef.current;
      const finalY = yLocked!;
      setXLocked(finalX);
      registerThrow(finalX, finalY);
    }
  };

  const registerThrow = (finalX: number, finalY: number) => {
    totalShots.current++;
    // Distance from center (0.5, 0.5), normalized 0–1
    const dx = finalX - 0.5;
    const dy = finalY - 0.5;
    const dist = Math.sqrt(dx * dx + dy * dy); // max ~0.707

    const pixelDist = dist * BOARD_SIZE;
    const hit = pixelDist <= TARGET_RADIUS;
    const isNear = pixelDist <= TARGET_RADIUS * 2.5;

    const dart = { x: finalX, y: finalY, hit };
    setThrownDarts(prev => [...prev, dart]);

    if (hit) {
      hits.current++;
      precisionScores.current.push(1 - dist / 0.5);
      setScore(prev => prev + 40);
    } else if (isNear) {
      precisionScores.current.push(Math.max(0, 1 - dist / 0.5));
      setScore(prev => prev + 15);
    }

    const nextChances = chancesLeft - 1;
    setChancesLeft(nextChances);

    if (nextChances <= 0) {
      setGameState('result');
      setTimeout(() => advanceLevel(), 1200);
    } else {
      // Reset for next attempt in same level
      setYLocked(null);
      setXLocked(null);
      setGameState('yAxis');
    }
  };

  const advanceLevel = () => {
    if (level >= TOTAL_DART_LEVELS) {
      finish();
    } else {
      const nextLives = hits.current === 0 && chancesLeft <= 0 ? lives - 1 : lives;
      if (nextLives < lives) {
        setLives(nextLives);
        if (nextLives <= 0) {
          onFail();
          return;
        }
      }
      setLevel(prev => prev + 1);
      setChancesLeft(4);
      setThrownDarts([]);
      setYLocked(null);
      setXLocked(null);
      setGameState('yAxis');
    }
  };

  const finish = () => {
    const accuracy = totalShots.current > 0 ? hits.current / totalShots.current : 0;
    const motor_baseline = precisionScores.current.length > 0
      ? precisionScores.current.reduce((a, b) => a + b, 0) / precisionScores.current.length
      : 0;

    const signals: BehavioralSignals = {
      accuracy,
      mean_response_time: 0,
      response_time_variance: 0,
      performance_decay: 0,
      retry_depth: 0,
      dropout_depth_index: 0,
      recovery_slope: motor_baseline
    };
    const livesBonus = lives * 100;
    const finalScore = score + livesBonus;
    onComplete(signals, finalScore, lives);
  };

  if (gameState === 'rules') {
    return (
      <GameRulesOverlay
        title="DART GAME"
        tag="MOTOR BASELINE"
        rules={[
          "A VERTICAL LINE WILL OSCILLATE UP AND DOWN ON THE BOARD",
          "PRESS SPACE (OR CLICK) TO LOCK THE VERTICAL POSITION (Y-AXIS)",
          "A HORIZONTAL LINE WILL THEN OSCILLATE SIDE TO SIDE",
          "PRESS SPACE (OR CLICK) AGAIN TO LOCK THE HORIZONTAL POSITION (X-AXIS)",
          "THE DART LANDS AT THEIR INTERSECTION — AIM FOR THE BULLSEYE",
          "YOU HAVE 4 THROWS PER LEVEL — SPEED INCREASES EACH LEVEL"
        ]}
        onStart={() => setGameState('yAxis')}
      />
    );
  }

  const hitColor = '#00C851';
  const missColor = '#FF2D2D';

  return (
    <NeoBrutalistLayout
      title="DART GAME"
      tag="MOTOR BASELINE"
      lives={lives}
      currentQuestion={level}
      totalQuestions={TOTAL_DART_LEVELS}
      score={score}
    >
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontWeight: 900, marginBottom: '16px', fontSize: '18px' }}>
          LEVEL {level} — SPEED: {speed.toFixed(1)}x — THROWS LEFT: {chancesLeft}
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
          <div
            onClick={handleThrow}
            style={{
              width: BOARD_SIZE,
              height: BOARD_SIZE,
              position: 'relative',
              background: '#f5f0e8',
              border: '4px solid #0a0a0a',
              boxShadow: '8px 8px 0 #0a0a0a',
              cursor: 'crosshair',
              overflow: 'hidden',
            }}
          >
            {/* Concentric rings */}
            {[160, 120, 80, 40, TARGET_RADIUS].map((r, i) => (
              <div key={i} style={{
                position: 'absolute',
                left: '50%', top: '50%',
                width: r * 2, height: r * 2,
                marginLeft: -r, marginTop: -r,
                borderRadius: '50%',
                border: `3px solid #0a0a0a`,
                background: 'transparent'
              }} />
            ))}
            {/* Bullseye */}
            <div style={{
              position: 'absolute',
              left: '50%', top: '50%',
              width: TARGET_RADIUS * 2, height: TARGET_RADIUS * 2,
              marginLeft: -TARGET_RADIUS, marginTop: -TARGET_RADIUS,
              borderRadius: '50%',
              background: '#FF2D2D',
              border: '3px solid #0a0a0a'
            }} />

            {/* Crosshair lines */}
            <div style={{ position: 'absolute', left: '50%', top: 0, width: '2px', height: '100%', background: 'rgba(0,0,0,0.2)', marginLeft: -1 }} />
            <div style={{ position: 'absolute', top: '50%', left: 0, height: '2px', width: '100%', background: 'rgba(0,0,0,0.2)', marginTop: -1 }} />

            {/* Y-axis moving line (visible in yAxis state) */}
            {gameState === 'yAxis' && (
              <div style={{
                position: 'absolute',
                top: `${yDisplay * 100}%`,
                left: 0, right: 0,
                height: '4px',
                background: '#0057FF',
                marginTop: -2
              }} />
            )}

            {/* X-axis moving line (visible in xAxis state, y is locked) */}
            {(gameState === 'xAxis') && (
              <>
                <div style={{
                  position: 'absolute',
                  top: `${yLocked! * 100}%`,
                  left: 0, right: 0,
                  height: '4px',
                  background: '#0057FF',
                  opacity: 0.5,
                  marginTop: -2
                }} />
                <div style={{
                  position: 'absolute',
                  left: `${xDisplay * 100}%`,
                  top: 0, bottom: 0,
                  width: '4px',
                  background: '#FFE500',
                  marginLeft: -2
                }} />
              </>
            )}

            {/* Thrown darts */}
            {thrownDarts.map((dart, i) => (
              <div key={i} style={{
                position: 'absolute',
                left: `${dart.x * 100}%`,
                top: `${dart.y * 100}%`,
                width: '16px', height: '16px',
                marginLeft: -8, marginTop: -8,
                borderRadius: '50%',
                background: dart.hit ? hitColor : missColor,
                border: '3px solid #0a0a0a',
                zIndex: 10
              }} />
            ))}

            {gameState === 'result' && (
              <div style={{
                position: 'absolute', inset: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: 'rgba(255,229,0,0.85)',
                fontSize: '28px', fontWeight: 900,
                fontFamily: 'Courier New, monospace',
                textTransform: 'uppercase'
              }}>
                {hits.current > 0 ? `${hits.current} HITS!` : 'NO HITS'}
              </div>
            )}
          </div>
        </div>

        <div style={{ marginTop: '16px' }}>
          {gameState === 'yAxis' && (
            <button className="neo-brutalist-button neo-brutalist-button--blue" style={{ fontSize: '20px', padding: '20px 48px' }} onClick={handleThrow}>
              [ LOCK Y-AXIS ]
            </button>
          )}
          {gameState === 'xAxis' && (
            <button className="neo-brutalist-button neo-brutalist-button--primary" style={{ fontSize: '20px', padding: '20px 48px' }} onClick={handleThrow}>
              [ LOCK X-AXIS & THROW ]
            </button>
          )}
        </div>
        <p style={{ marginTop: '16px', fontWeight: 900, fontSize: '14px' }}>PRESS SPACE OR CLICK TO ACT</p>
      </div>
    </NeoBrutalistLayout>
  );
};
