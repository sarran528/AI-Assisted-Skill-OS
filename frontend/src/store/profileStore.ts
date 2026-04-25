import { create } from 'zustand';

interface ProfileVector {
  id: string;
  user_id: string;
  version: number;
  cognitive_capacity: number;
  attention_stability: number;
  learning_tolerance: number;
  motor_baseline: number;
  stress_resilience: number;
  time_constraint: number;
  raw_signals: Record<string, unknown>;
  created_at: string;
}

interface ProfileStore {
  profile: ProfileVector | null;
  parameters: Record<string, number> | null;
  setProfile: (profile: ProfileVector) => void;
  setParameters: (params: Record<string, number>) => void;
  clear: () => void;
}

export const useProfileStore = create<ProfileStore>((set) => ({
  profile: null,
  parameters: null,
  setProfile: (profile) => set({ profile }),
  setParameters: (parameters) => set({ parameters }),
  clear: () => set({ profile: null, parameters: null }),
}));
