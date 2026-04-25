import axiosClient from "./axiosClient";
import type { CheckpointValidationResponse } from "../types";

export async function validateCheckpoint(payload: {
  sessionId: string;
  checkpointId: string;
}): Promise<CheckpointValidationResponse> {
  const response = await axiosClient.post("checkpoint/validate", {
    session_id: payload.sessionId,
    checkpoint_id: payload.checkpointId,
  });
  return response.data;
}
