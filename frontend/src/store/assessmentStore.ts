import { create } from 'zustand';

interface AssessmentStore {
  sessionId: string | null;
  completedLevels: string[];
  currentLevel: string | null;
  lives: number;
  profileActive: boolean;
  setSessionId: (id: string) => void;
  setCurrentLevel: (levelId: string) => void;
  setLives: (count: number) => void;
  markLevelComplete: (levelId: string) => void;
  setProfileActive: (active: boolean) => void;
  reset: () => void;
}

export const useAssessmentStore = create<AssessmentStore>((set) => ({
  sessionId: null,
  completedLevels: [],
  currentLevel: null,
  lives: 3,
  profileActive: false,
  setSessionId: (id) => set({ sessionId: id }),
  setCurrentLevel: (levelId) => set({ currentLevel: levelId }),
  setLives: (count) => set({ lives: count }),
  markLevelComplete: (levelId) =>
    set((state) => ({
      completedLevels: [...state.completedLevels, levelId],
    })),
  setProfileActive: (active) => set({ profileActive: active }),
  reset: () => set({
    sessionId: null,
    completedLevels: [],
    currentLevel: null,
    lives: 3,
    profileActive: false,
  }),
}));
