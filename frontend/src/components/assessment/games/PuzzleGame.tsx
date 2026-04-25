import React, { useState, useEffect, useRef } from 'react';
import { NeoBrutalistLayout } from '../NeoBrutalistLayout';
import { GameRulesOverlay } from '../GameRulesOverlay';
import { BehavioralSignals } from '../../../stores/assessmentStore';
import { isSolvable } from '../../../utils/puzzleSolvability';

interface PuzzleGameProps {
  onComplete: (signals: BehavioralSignals, score: number, livesRemaining: number) => void;
  onFail: () => void;
}

const LEVELS = [
  { size: 2, timeLimit: 30000, label: '2X2' },
  { size: 3, timeLimit: 60000, label: '3X3' },
  { size: 4, timeLimit: 120000, label: '4X4' },
];
const TOTAL_PUZZLES = LEVELS.length;

export const PuzzleGame: React.FC<PuzzleGameProps> = ({ onComplete, onFail }) => {
  const [gameState, setGameState] = useState<'rules' | 'playing' | 'solved'>('rules');
  const [question, setQuestion] = useState(0); // index into LEVELS
  const [lives, setLives] = useState(3);
  const [score, setScore] = useState(0);
  const [tiles, setTiles] = useState<number[]>([]);
  const [moves, setMoves] = useState(0);
  const [timeLeft, setTimeLeft] = useState(30000);
  const [isGameOver, setIsGameOver] = useState(false);

  const retryDepth = useRef(0);
  const totalAttemptedClicks = useRef(0);
  const totalValidMoves = useRef(0);
  const solveTimes = useRef<number[]>([]);
  const startTime = useRef<number>(0);
  const solveTimeSnap = useRef<number>(0); // captured at solve-detection
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const config = LEVELS[question];

  const generatePuzzle = () => {
    const size = config.size;
    const n = size * size;
    const newTiles = Array.from({ length: n }, (_, i) => i);

    let attempts = 0;
    do {
      for (let i = n - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [newTiles[i], newTiles[j]] = [newTiles[j], newTiles[i]];
      }
      attempts++;
    } while ((!isSolvable(newTiles, size) || isSolved(newTiles)) && attempts < 1000);

    setTiles(newTiles);
    setMoves(0);
    setTimeLeft(config.timeLimit);
    startTime.current = Date.now();
  };

  const isSolved = (t: number[]) => {
    // Solved = [1, 2, 3, ..., n-1, 0] — tiles in order, empty at end
    for (let i = 0; i < t.length - 1; i++) {
      if (t[i] !== i + 1) return false;
    }
    return t[t.length - 1] === 0;
  };

  const startPlaying = () => {
    setGameState('playing');
    generatePuzzle();
  };

  // Timer
  useEffect(() => {
    if (gameState !== 'playing' || isGameOver) return;

    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 100) {
          handleTimeOut();
          return 0;
        }
        return prev - 100;
      });
    }, 100);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [question, gameState, isGameOver]);

  const handleTimeOut = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    const nextLives = lives - 1;
    setLives(nextLives);
    if (nextLives <= 0) {
      setIsGameOver(true);
      setTimeout(onFail, 1000);
    } else {
      retryDepth.current++;
      generatePuzzle();
    }
  };

  const handleTileClick = (index: number) => {
    if (isGameOver || gameState !== 'playing') return;
    totalAttemptedClicks.current++;

    const size = config.size;
    const emptyIdx = tiles.indexOf(0);

    const row = Math.floor(index / size);
    const col = index % size;
    const emptyRow = Math.floor(emptyIdx / size);
    const emptyCol = emptyIdx % size;

    const isAdjacent =
      (Math.abs(row - emptyRow) === 1 && col === emptyCol) ||
      (Math.abs(col - emptyCol) === 1 && row === emptyRow);

    if (isAdjacent) {
      const newTiles = [...tiles];
      [newTiles[index], newTiles[emptyIdx]] = [newTiles[emptyIdx], newTiles[index]];
      setTiles(newTiles);
      setMoves(prev => prev + 1);
      totalValidMoves.current++;

      if (isSolved(newTiles)) {
        if (timerRef.current) clearInterval(timerRef.current);
        solveTimeSnap.current = Date.now() - startTime.current; // capture exact solve time
        setGameState('solved');
      }
    }
  };

  const handleSubmit = () => {
    solveTimes.current.push(solveTimeSnap.current);

    const bonus = Math.floor((timeLeft / config.timeLimit) * 20);
    setScore(prev => prev + 20 + bonus);

    if (question >= TOTAL_PUZZLES - 1) {
      finish();
    } else {
      setQuestion(prev => prev + 1);
      setGameState('playing');
    }
  };

  // generate puzzle whenever question changes while playing
  useEffect(() => {
    if (gameState === 'playing' && question > 0) {
      generatePuzzle();
    }
  }, [question]);

  const finish = () => {
    const motorBaseline =
      totalAttemptedClicks.current > 0
        ? totalValidMoves.current / totalAttemptedClicks.current
        : 0;

    const avgSolveTime =
      solveTimes.current.length > 0
        ? solveTimes.current.reduce((a, b) => a + b, 0) / solveTimes.current.length
        : 0;

    const signals: BehavioralSignals = {
      accuracy: 1.0,
      mean_response_time: avgSolveTime,
      response_time_variance: 0,
      performance_decay: 0,
      retry_depth: retryDepth.current,
      dropout_depth_index: 0,
      recovery_slope: 0,
    };

    onComplete(signals, score, lives);
  };

  if (gameState === 'rules') {
    return (
      <GameRulesOverlay
        title="PUZZLE GAME"
        tag="WORKING MEMORY"
        rules={[
          'SLIDE THE TILES TO ARRANGE THEM IN NUMERICAL ORDER',
          'CLICK A TILE ADJACENT TO THE EMPTY SPOT TO MOVE IT',
          'YOU WILL SOLVE ONE 2X2, ONE 3X3, AND ONE 4X4 PUZZLE',
          'SOLVE BEFORE THE TIMER RUNS OUT — THEN HIT SUBMIT',
          'SPEED IS REWARDED WITH BONUS POINTS',
        ]}
        onStart={startPlaying}
      />
    );
  }

  return (
    <NeoBrutalistLayout
      title="PUZZLE GAME"
      tag="WORKING MEMORY"
      lives={lives}
      currentQuestion={question + 1}
      totalQuestions={TOTAL_PUZZLES}
      score={score}
    >
      <div
        className="neo-brutalist-card"
        style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}
      >
        <div
          style={{
            marginBottom: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            fontWeight: 900,
          }}
        >
          <span>MOVES: {moves}</span>
          <span>TIME: {(timeLeft / 1000).toFixed(1)}S</span>
          <span>GRID: {config.label}</span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${config.size}, 1fr)`,
            gap: '12px',
            background: '#0a0a0a',
            padding: '12px',
            border: '3px solid #0a0a0a',
          }}
        >
          {tiles.map((tile, i) => (
            <div
              key={i}
              onClick={() => handleTileClick(i)}
              className={tile === 0 ? '' : 'neo-brutalist-button'}
              style={{
                height: config.size === 2 ? '180px' : config.size === 3 ? '120px' : '90px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '32px',
                fontWeight: 900,
                background: tile === 0 ? 'transparent' : '#fff',
                cursor: tile === 0 ? 'default' : 'pointer',
                border: tile === 0 ? 'none' : '3px solid #0a0a0a',
                visibility: tile === 0 ? 'hidden' : 'visible',
              }}
            >
              {tile}
            </div>
          ))}
        </div>

        <p style={{ marginTop: '24px', fontWeight: 900 }}>
          ARRANGE TILES IN ORDER (1 → {config.size * config.size - 1}), EMPTY SPACE GOES LAST
        </p>

        {gameState === 'solved' && (
          <button
            className="neo-brutalist-button neo-brutalist-button--success"
            style={{ marginTop: '24px', width: '100%', fontSize: '24px', padding: '20px' }}
            onClick={handleSubmit}
          >
            {question >= TOTAL_PUZZLES - 1 ? '✓ SUBMIT & FINISH' : '✓ SUBMIT & NEXT PUZZLE'}
          </button>
        )}
      </div>
    </NeoBrutalistLayout>
  );
};
