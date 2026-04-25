import { create } from 'zustand';
import { getAttemptLabel } from '../utils/attemptLabel';

export interface BehavioralSignals {
  accuracy: number;
  mean_response_time: number;
  response_time_variance: number;
  performance_decay: number;
  retry_depth: number;
  dropout_depth_index: number;
  recovery_slope: number;
}

export interface TimeSignals {
  available_hours_per_week: number;
  preferred_session_length: number;
  schedule_reliability: number;
  flex_buffer: number;
}

export interface GameState {
  attempts: number;
  attemptLabel: string;
  bestScore: number;
  lastLivesRemaining: number;
  completed: boolean;
  signals: BehavioralSignals;
  timeSignals?: TimeSignals; // Only for Game 6
}

export const GAME_IDS = [1, 2, 3, 4, 5, 6] as const;
export type GameId = typeof GAME_IDS[number];

interface AssessmentStore {
  games: Record<GameId, GameState>;
  finishLevel: (
    gameId: GameId,
    signals: BehavioralSignals,
    timeSignals: TimeSignals | undefined,
    livesRemaining: number,
    score: number,
    completed: boolean
  ) => void;
  resetAssessment: () => void;
  allLevelsComplete: () => boolean;
}

const initialGameState = (): GameState => ({
  attempts: 0,
  attemptLabel: 'never',
  bestScore: 0,
  lastLivesRemaining: 0,
  completed: false,
  signals: {
    accuracy: 0,
    mean_response_time: 0,
    response_time_variance: 0,
    performance_decay: 0,
    retry_depth: 0,
    dropout_depth_index: 0,
    recovery_slope: 0,
  },
});

export const useAssessmentStore = create<AssessmentStore>((set, get) => ({
  games: {
    1: initialGameState(),
    2: initialGameState(),
    3: initialGameState(),
    4: initialGameState(),
    5: initialGameState(),
    6: initialGameState(),
  },
  finishLevel: (gameId, signals, timeSignals, livesRemaining, score, completed) => {
    set((state) => {
      const game = state.games[gameId];
      const newAttempts = game.attempts + 1;
      return {
        games: {
          ...state.games,
          [gameId]: {
            ...game,
            attempts: newAttempts,
            attemptLabel: getAttemptLabel(newAttempts),
            bestScore: Math.max(game.bestScore, score),
            lastLivesRemaining: livesRemaining,
            completed: game.completed || completed,
            signals: { ...signals },
            ...(timeSignals ? { timeSignals: { ...timeSignals } } : {}),
          },
        },
      };
    });
  },
  resetAssessment: () => {
    set({
      games: {
        1: initialGameState(),
        2: initialGameState(),
        3: initialGameState(),
        4: initialGameState(),
        5: initialGameState(),
        6: initialGameState(),
      },
    });
  },
  allLevelsComplete: () => {
    const { games } = get();
    // ProfileVector computation relies on all levels being completed at least once
    return GAME_IDS.every((id) => games[id].attempts > 0);
  },
}));
