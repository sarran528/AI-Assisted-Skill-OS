import { create } from 'zustand';

interface BaselineState {
  skill_id: string;
  exposure_score: number;
  declarative_knowledge: number;
  confidence_bias: number;
  adjusted_repetition_intensity: number;
}

interface PhaseSchema {
  phase_slug: string;
  competencies: string[];
  techniques: string[];
  checkpoints: string[];
  estimated_hours: number;
  status: 'locked' | 'active' | 'completed';
}

interface RoadmapResponse {
  id: string;
  skill_id: string;
  profile_version: number;
  phases: PhaseSchema[];
  status: string;
  created_at: string;
}

interface RoadmapStore {
  targetSkillId: string | null;
  baseline: BaselineState | null;
  roadmap: RoadmapResponse | null;
  setTargetSkill: (skillId: string) => void;
  setBaseline: (baseline: BaselineState) => void;
  setRoadmap: (roadmap: RoadmapResponse) => void;
  clear: () => void;
}

export const useRoadmapStore = create<RoadmapStore>((set) => ({
  targetSkillId: null,
  baseline: null,
  roadmap: null,
  setTargetSkill: (skillId) => set({ targetSkillId: skillId }),
  setBaseline: (baseline) => set({ baseline }),
  setRoadmap: (roadmap) => set({ roadmap }),
  clear: () => set({ targetSkillId: null, baseline: null, roadmap: null }),
}));
