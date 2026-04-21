import axiosClient from './axiosClient';

export interface TipResponse {
  tip: string;
  trigger_reason: string;
}

export const tipApi = {
  getTip: (sessionId: string) =>
    axiosClient.get<TipResponse>(`/tip/${sessionId}`),
};
