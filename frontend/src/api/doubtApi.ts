import axiosClient from './axiosClient';

export interface DoubtRequest {
  session_id: string;
  phase: string;
  technique_id: string;
  user_query: string;
}

export interface DoubtResponse {
  explanation: string;
  sources_used: number;
}

export const doubtApi = {
  askDoubt: (data: DoubtRequest) =>
    axiosClient.post<DoubtResponse>('/doubt/ask', data),
};
