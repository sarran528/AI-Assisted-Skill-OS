import { apiClient } from "./client";
import type { Session, SessionCompleteResponse, SessionListItem, SessionMetricsPayload, SessionStartResponse } from "../types";

export async function getSession(sessionId: string): Promise<Session> {
  const response = await apiClient.get(`/sessions/${sessionId}`);
  return response.data;
}

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

export async function getRecentSessions(limit = 5): Promise<SessionListItem[]> {
  const response = await apiClient.get("/sessions/recent", { params: { limit } });
  return response.data.items ?? [];
}
