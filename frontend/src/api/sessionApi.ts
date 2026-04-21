import axiosClient from './axiosClient';

export interface SessionStartRequest {
  roadmap_id: string;
  phase: string;
  technique_id: string;
}

export interface SessionStartResponse {
  session_id: string;
  status: string;
}

export interface SessionMetricsSubmit {
  session_id: string;
  accuracy: number;
  response_time: number;
  error_count: number;
  step_completion_log: string[];
}

export interface SessionCompleteResponse {
  session_id: string;
  status: 'completed' | 'failed';
  violations: string[];
}

export const sessionApi = {
  startSession: (data: SessionStartRequest) =>
    axiosClient.post<SessionStartResponse>('/session/start', data),

  submitMetrics: (data: SessionMetricsSubmit) =>
    axiosClient.post<{ received: boolean }>('/session/metrics', data),

  completeSession: (sessionId: string) =>
    axiosClient.post<SessionCompleteResponse>('/session/complete', { session_id: sessionId }),

  getSession: (sessionId: string) =>
    axiosClient.get(`/session/${sessionId}`),
};
