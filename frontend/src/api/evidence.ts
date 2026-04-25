import axiosClient from "./axiosClient";
import type { EvidenceUploadResponse } from "../types";

export async function uploadEvidence(payload: {
  sessionId: string;
  checkpointId: string;
  file: File;
  evidenceType?: string;
}): Promise<EvidenceUploadResponse> {
  const formData = new FormData();
  formData.append("session_id", payload.sessionId);
  formData.append("checkpoint_id", payload.checkpointId);
  formData.append("evidence_type", payload.evidenceType ?? "artifact");
  formData.append("file", payload.file);

  const response = await axiosClient.post("/evidence/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}
