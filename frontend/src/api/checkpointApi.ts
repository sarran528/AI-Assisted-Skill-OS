import axiosClient from './axiosClient';

export interface CheckpointValidateRequest {
  session_id: string;
  checkpoint_id: string;
}

export interface CheckpointValidateResponse {
  checkpoint_id: string;
  passed: boolean;
  threshold_used: number;
  actual_value: number;
  detail: string;
}

export const checkpointApi = {
  listCheckpoints: (roadmapId: string) =>
    axiosClient.get<Array<{ checkpoint_id: string; status: string; phase: string }>>(
      `/checkpoint/${roadmapId}`
    ),

  validateCheckpoint: (data: CheckpointValidateRequest) =>
    axiosClient.post<CheckpointValidateResponse>('/checkpoint/validate', data),
};
