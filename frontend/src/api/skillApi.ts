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
}

export interface SkillResearchComposeRequest {
  skill_id: string;
  why_learn: string;
  experience_level: "beginner" | "intermediate" | "advanced";
  has_required_tools: boolean;
  hours_per_week: number;
  target_goal: "hobby" | "professional" | "exam";
}

export interface SkillResearchComposeResponse {
  skill_id: string;
  status: string;
  roadmap_job_id: string;
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
};
