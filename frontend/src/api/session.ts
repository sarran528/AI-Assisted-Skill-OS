import axiosClient from "./axiosClient";
import type { Session, SessionCompleteResponse, SessionListItem, SessionMetricsPayload, SessionStartResponse } from "../types";

export async function getSession(sessionId: string): Promise<Session> {
  const response = await axiosClient.get(`/session/${sessionId}`);
  return response.data;
}

export async function startSession(payload: {
  skill_id: string;
  phase: string;
  technique_id: string;
}): Promise<SessionStartResponse> {
  const response = await axiosClient.post("session/start", payload);
  return response.data;
}

export async function submitSessionMetrics(payload: SessionMetricsPayload): Promise<unknown> {
  const { session_id, ...metrics } = payload;
  const response = await axiosClient.post("session/metrics", {
    session_id,
    metrics,
  });
  return response.data;
}

export async function completeSession(payload: {
  session_id: string;
  completed_steps: string[];
}): Promise<SessionCompleteResponse> {
  const response = await axiosClient.post("session/complete", payload);
  return response.data;
}

export async function getRecentSessions(limit = 5): Promise<SessionListItem[]> {
  const response = await axiosClient.get("session/recent", { params: { limit } });
  return response.data.items ?? [];
}
