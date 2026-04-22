import axiosClient from './axiosClient';

export interface RoadmapGenerateRequest {
  skill_id: string;
}

export interface RoadmapGenerateResponse {
  job_id: string;
  status: string;
}

export interface PhaseSchema {
  phase_slug: string;
  competencies: string[];
  techniques: string[];
  checkpoints: string[];
  estimated_hours: number;
  status: 'locked' | 'active' | 'completed';
}

export interface RoadmapResponse {
  id: string;
  skill_id: string;
  profile_version: number;
  phases: PhaseSchema[];
  status: string;
  created_at: string;
}

export const roadmapApi = {
  generateRoadmap: (data: RoadmapGenerateRequest) =>
    axiosClient.post<RoadmapGenerateResponse>('/roadmap/generate', data),

  getRoadmap: (userId: string) =>
    axiosClient.get<RoadmapResponse>(`/roadmap/${userId}`),

  getRoadmapStatus: (userId: string) =>
    axiosClient.get<{ status: string; job_id: string | null }>(`/roadmap/${userId}/status`),

  abandonRoadmap: (roadmapId: string) =>
    axiosClient.patch<{ status: string }>(`/roadmap/${roadmapId}/abandon`),
};
