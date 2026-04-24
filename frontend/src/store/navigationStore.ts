import { create } from "zustand";
import { persist } from "zustand/middleware";

export type SystemState =
  | "assessment_incomplete"
  | "profile_active"
  | "roadmap_generation"
  | "roadmap_active"
  | "session_active";

export type AssessmentLevelStatus =
  | "not_started"
  | "in_progress"
  | "complete"
  | "failed";

export interface RoadmapCheckpoint {
  id: string;
  description: string;
  threshold: string;
  status: "pending" | "attempted" | "passed" | "failed" | "validating" | "locked";
  validationReason?: string;
  retriesRemaining: number;
}

export interface RoadmapTechnique {
  id: string;
  name: string;
  status: "locked" | "active" | "complete";
  checkpoints: RoadmapCheckpoint[];
}

export interface RoadmapCompetency {
  name: string;
  techniques: RoadmapTechnique[];
}

export interface RoadmapPhase {
  id: string;
  name: string;
  status: "locked" | "active" | "complete";
  competencies: RoadmapCompetency[];
}

export interface NavigationState {
  systemState: SystemState;

  assessmentProgress: {
    [level: number]: {
      status: AssessmentLevelStatus;
      attempts: number;
      livesRemaining: number;
      completedAt?: string;
      questionsAnswered?: number;
    };
  };

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

  currentSkill: {
    skillId: string | null;
    skillName: string | null;
    domain: string | null;
  };

  roadmapState: {
    isGenerated: boolean;
    isGenerating: boolean;
    currentPhase: string | null;
    currentTechnique: string | null;
    phases: RoadmapPhase[];
    roadmapComplete: boolean;
  };

  sessionState: {
    isActive: boolean;
    sessionId: string | null;
    currentStep: number;
    totalSteps: number;
    retryCount: number;
    maxRetries: number;
  };

  setSystemState: (state: SystemState) => void;
  updateAssessmentLevel: (level: number, update: Partial<NavigationState["assessmentProgress"][number]>) => void;
  setProfileState: (profile: Partial<NavigationState["profileState"]>) => void;
  setCurrentSkill: (skill: Partial<NavigationState["currentSkill"]>) => void;
  setRoadmapState: (roadmap: Partial<NavigationState["roadmapState"]>) => void;
  setRoadmapPhases: (phases: RoadmapPhase[]) => void;
  updateCheckpointStatus: (
    phaseId: string,
    techniqueId: string,
    checkpointId: string,
    status: RoadmapCheckpoint["status"],
    validationReason?: string
  ) => void;
  promoteNextPhaseIfNeeded: () => void;
  setSessionState: (session: Partial<NavigationState["sessionState"]>) => void;
  resetNavigation: () => void;
}

const initialState = {
  systemState: "assessment_incomplete" as SystemState,

  assessmentProgress: {
    1: { status: "not_started" as const, attempts: 0, livesRemaining: 3 },
    2: { status: "not_started" as const, attempts: 0, livesRemaining: 3 },
    3: { status: "not_started" as const, attempts: 0, livesRemaining: 3 },
    4: { status: "not_started" as const, attempts: 0, livesRemaining: 3 },
    5: { status: "not_started" as const, attempts: 0, livesRemaining: 3 },
    6: { status: "not_started" as const, attempts: 0, livesRemaining: 3 },
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
    isGenerating: false,
    currentPhase: null,
    currentTechnique: null,
    phases: [],
    roadmapComplete: false,
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
    (set) => ({
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

      setRoadmapPhases: (phases) =>
        set((state) => ({
          roadmapState: {
            ...state.roadmapState,
            phases,
          },
        })),

      updateCheckpointStatus: (phaseId, techniqueId, checkpointId, status, validationReason) =>
        set((state) => ({
          roadmapState: {
            ...state.roadmapState,
            phases: state.roadmapState.phases.map((phase) =>
              phase.id !== phaseId
                ? phase
                : {
                    ...phase,
                    competencies: phase.competencies.map((competency) => ({
                      ...competency,
                      techniques: competency.techniques.map((technique) =>
                        technique.id !== techniqueId
                          ? technique
                          : {
                              ...technique,
                              checkpoints: technique.checkpoints.map((checkpoint) =>
                                checkpoint.id !== checkpointId
                                  ? checkpoint
                                  : {
                                      ...checkpoint,
                                      status,
                                      validationReason,
                                      retriesRemaining:
                                        status === "failed"
                                          ? Math.max(0, checkpoint.retriesRemaining - 1)
                                          : checkpoint.retriesRemaining,
                                    }
                              ),
                            }
                      ),
                    })),
                  }
            ),
          },
        })),

      promoteNextPhaseIfNeeded: () =>
        set((state) => {
          const updatedPhases = [...state.roadmapState.phases];
          const activeIndex = updatedPhases.findIndex((phase) => phase.status === "active");

          if (activeIndex < 0) {
            return state;
          }

          const activePhase = updatedPhases[activeIndex];
          const hasPending = activePhase.competencies.some((c) =>
            c.techniques.some((t) => t.checkpoints.some((cp) => cp.status !== "passed"))
          );

          if (hasPending) {
            return state;
          }

          updatedPhases[activeIndex] = { ...activePhase, status: "complete" };
          const nextIndex = activeIndex + 1;
          if (updatedPhases[nextIndex]) {
            updatedPhases[nextIndex] = { ...updatedPhases[nextIndex], status: "active" };
          }

          const nextActive = updatedPhases.find((phase) => phase.status === "active");
          return {
            roadmapState: {
              ...state.roadmapState,
              phases: updatedPhases,
              currentPhase: nextActive?.name ?? null,
              roadmapComplete: !updatedPhases.some((phase) => phase.status !== "complete"),
            },
          };
        }),

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
