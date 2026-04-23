import { create } from "zustand";
import { persist } from "zustand/middleware";

// System flow states based on the spec
export type SystemState = 
  | 'assessment_incomplete'  // User hasn't completed all 6 assessment levels
  | 'profile_inactive'       // Assessment complete but profile not built
  | 'skill_selection'        // Profile active, need to select skill
  | 'roadmap_generation'     // Skill selected, roadmap generating
  | 'roadmap_active'          // Roadmap generated and active
  | 'session_active'          // Currently in a session
  | 'checkpoint_pending'      // Evidence submission required;

export interface NavigationState {
  // System state tracking
  systemState: SystemState;
  
  // Assessment progress (6 levels)
  assessmentProgress: {
    [level: number]: {
      status: 'locked' | 'incomplete' | 'in_progress' | 'complete';
      score?: number;
      livesRemaining?: number;
      questionsAnswered?: number;
    };
  };
  
  // Profile state (6 dimensions)
  profileState: {
    isActive: boolean;
    dimensions: {
      cognitive_capacity: number;
      attention_stability: number;
      learning_tolerance: number;
      motor_baseline: number;
      stress_resilience: number;
      time_constraint: number;
    };
  };
  
  // Current skill and roadmap
  currentSkill: {
    skillId: string | null;
    skillName: string | null;
    domain: string | null;
  };
  
  roadmapState: {
    isGenerated: boolean;
    currentPhase: string | null;
    currentTechnique: string | null;
    phasesCompleted: string[];
    checkpointsCompleted: string[];
  };
  
  // Session state
  sessionState: {
    isActive: boolean;
    sessionId: string | null;
    currentStep: number;
    totalSteps: number;
    retryCount: number;
    maxRetries: number;
  };
  
  // Actions
  setSystemState: (state: SystemState) => void;
  updateAssessmentLevel: (level: number, status: any) => void;
  setProfileState: (profile: any) => void;
  setCurrentSkill: (skill: any) => void;
  setRoadmapState: (roadmap: any) => void;
  setSessionState: (session: any) => void;
  resetNavigation: () => void;
}

const initialState = {
  systemState: 'assessment_incomplete' as SystemState,
  
  assessmentProgress: {
    1: { status: 'incomplete' as const },
    2: { status: 'locked' as const },
    3: { status: 'locked' as const },
    4: { status: 'locked' as const },
    5: { status: 'locked' as const },
    6: { status: 'locked' as const },
  },
  
  profileState: {
    isActive: false,
    dimensions: {
      cognitive_capacity: 0,
      attention_stability: 0,
      learning_tolerance: 0,
      motor_baseline: 0,
      stress_resilience: 0,
      time_constraint: 0,
    },
  },
  
  currentSkill: {
    skillId: null,
    skillName: null,
    domain: null,
  },
  
  roadmapState: {
    isGenerated: false,
    currentPhase: null,
    currentTechnique: null,
    phasesCompleted: [],
    checkpointsCompleted: [],
  },
  
  sessionState: {
    isActive: false,
    sessionId: null,
    currentStep: 0,
    totalSteps: 0,
    retryCount: 0,
    maxRetries: 3,
  },
};

export const useNavigationStore = create<NavigationState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      setSystemState: (systemState) => set({ systemState }),
      
      updateAssessmentLevel: (level, update) => set((state) => ({
        assessmentProgress: {
          ...state.assessmentProgress,
          [level]: {
            ...state.assessmentProgress[level],
            ...update,
          },
        },
      })),
      
      setProfileState: (profile) => set((state) => ({
        profileState: {
          ...state.profileState,
          ...profile,
        },
      })),
      
      setCurrentSkill: (skill) => set((state) => ({
        currentSkill: {
          ...state.currentSkill,
          ...skill,
        },
      })),
      
      setRoadmapState: (roadmap) => set((state) => ({
        roadmapState: {
          ...state.roadmapState,
          ...roadmap,
        },
      })),
      
      setSessionState: (session) => set((state) => ({
        sessionState: {
          ...state.sessionState,
          ...session,
        },
      })),
      
      resetNavigation: () => set(initialState),
    }),
    {
      name: "skillos-navigation",
    }
  )
);
