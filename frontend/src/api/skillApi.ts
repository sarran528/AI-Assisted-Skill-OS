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

export const skillApi = {
  listSkills: () =>
    axiosClient.get<Array<{ skill_id: string; name: string; complexity: number }>>('/skill/list'),

  submitBaseline: (data: GroundingProbeSubmit) =>
    axiosClient.post<BaselineStateResponse>('/skill/baseline', data),

  getBaseline: (skillId: string) =>
    axiosClient.get<BaselineStateResponse>(`/skill/${skillId}/baseline`),
};
