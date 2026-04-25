import axiosClient from './axiosClient';

export interface ProfileVectorResponse {
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

export const profileApi = {
  getProfile: (userId: string) =>
    axiosClient.get<ProfileVectorResponse>(`profile/${userId}`),

  getParameters: (userId: string) =>
    axiosClient.get<Record<string, number>>(`profile/${userId}/parameters`),

  getHistory: (userId: string) =>
    axiosClient.get<ProfileVectorResponse[]>(`profile/${userId}/history`),
};
