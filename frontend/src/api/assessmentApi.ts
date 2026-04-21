import axiosClient from './axiosClient';

export interface RawSignalSubmit {
  level_id: string;
  accuracy: number;
  mean_response_time: number;
  response_time_variance: number;
  performance_decay: number;
  retry_depth: number;
  dropout_depth_index: number;
  recovery_slope: number;
  available_hours_per_week?: number;
  preferred_session_length?: number;
}

export interface AssessmentCompleteResponse {
  profile_id: string;
  cognitive_capacity: number;
  attention_stability: number;
  learning_tolerance: number;
  motor_baseline: number;
  stress_resilience: number;
  time_constraint: number;
  version: number;
}

export const assessmentApi = {
  startSession: () =>
    axiosClient.post<{ session_id: string }>('/assessment/start', {}),

  submitSignals: (data: RawSignalSubmit) =>
    axiosClient.post<{ level_id: string; received: boolean }>('/assessment/submit', data),

  completeAssessment: (sessionId: string) =>
    axiosClient.post<AssessmentCompleteResponse>('/assessment/complete', { session_id: sessionId }),

  getStatus: () =>
    axiosClient.get<{ levels_completed: string[]; profile_active: boolean }>('/assessment/status'),
};
