import { apiClient } from "./client";
import type { SessionCompleteResponse, SessionMetricsPayload, SessionStartResponse } from "../types";

export async function startSession(payload: {
  skill_id: string;
  phase: string;
  technique_id: string;
}): Promise<SessionStartResponse> {
  const response = await apiClient.post("/sessions/start", payload);
  return response.data;
}

export async function submitSessionMetrics(payload: SessionMetricsPayload): Promise<unknown> {
  const response = await apiClient.post("/sessions/metrics", payload);
  return response.data;
}

export async function completeSession(payload: {
  session_id: string;
  completed_steps: string[];
}): Promise<SessionCompleteResponse> {
  const response = await apiClient.post("/sessions/complete", payload);
  return response.data;
}
