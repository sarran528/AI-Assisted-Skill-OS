import axiosClient from './axiosClient';

export interface GroundingProbeSubmit {
  skill_id: string;
  recognition_score: number;
  declarative_score: number;
  confidence_bias: number;
}

export interface BaselineStateResponse {
  skill_id: string;
  exposure_score: number;
  declarative_knowledge: number;
  confidence_bias: number;
  adjusted_repetition_intensity: number;
}

export interface DiscoverSkillRequest {
  skill_name: string;
  domain?: string;
  complexity_score?: number;
}

export interface DiscoverSkillResponse {
  skill_id: string;
  name: string;
  domain: string;
  complexity_score: number;
  version: number;
  created: boolean;
  status: string;
  job_id: string;
}

export interface SkillResearchComposeRequest {
  skill_id: string;
  why_learn: string;
  experience_level: "beginner" | "intermediate" | "advanced";
  has_required_tools: boolean;
  hours_per_week: number;
  target_goal: "hobby" | "professional" | "exam";
  dynamic_answers: Record<string, any>;
}

export interface SkillQuestion {
  id: string;
  text: string;
  type: "single_select" | "multi_select" | "numeric" | "slider";
  options?: string[];
  min?: number;
  max?: number;
  step?: number;
}

export interface SkillAnalysis {
  skill_name: string;
  complexity_score: number;
  prerequisite_gaps: string[];
  estimated_phases: string[];
  common_failure_modes: string[];
}

export interface SkillAnalysisResponse {
  analysis: SkillAnalysis;
  questions: SkillQuestion[];
}

export interface SkillResearchComposeResponse {
  skill_id: string;
  status: string;
  roadmap_job_id: string;
  research_job_id: string;
}

export const skillApi = {
  listSkills: async () => {
    const response = await axiosClient.get<Array<{ skill_id: string; name: string; complexity_score: number }>>(
      '/skill/list'
    );
    return {
      data: response.data.map((item) => ({
        skill_id: item.skill_id,
        name: item.name,
        complexity: item.complexity_score,
      })),
    };
  },

  submitBaseline: (data: GroundingProbeSubmit) =>
    axiosClient.post<BaselineStateResponse>('/skill/baseline', data),

  getBaseline: (skillId: string) =>
    axiosClient.get<BaselineStateResponse>(`/skill/${skillId}/baseline`),

  discoverSkill: (data: DiscoverSkillRequest) =>
    axiosClient.post<DiscoverSkillResponse>('/skill/discover', data),

  composeResearch: (data: SkillResearchComposeRequest) =>
    axiosClient.post<SkillResearchComposeResponse>('/skill/research/compose', data),

  analyzeSkill: (skillName: string) =>
    axiosClient.post<SkillAnalysisResponse>('/skill/analyze', { skill_name: skillName }),
};
