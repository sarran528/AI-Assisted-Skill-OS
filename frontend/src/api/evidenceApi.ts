import axiosClient from './axiosClient';

export interface EvidenceUploadResponse {
  evidence_id: string;
  artifact_url: string;
  type: string;
}

export interface EvidenceRecord {
  id: string;
  session_id: string;
  checkpoint_id: string;
  type: string;
  validated: boolean;
  validation_result: Record<string, unknown> | null;
}

export const evidenceApi = {
  uploadEvidence: (formData: FormData) =>
    axiosClient.post<EvidenceUploadResponse>('/evidence/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  getEvidence: (sessionId: string) =>
    axiosClient.get<EvidenceRecord[]>(`/evidence/${sessionId}`),
};
