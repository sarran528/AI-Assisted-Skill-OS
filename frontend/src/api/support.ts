import { apiClient } from "./client";
import type {
  DoubtAnswerResponse,
  SupportResourcesResponse,
  TipResponse,
} from "../types";

export async function askDoubt(payload: {
  skill_id: string;
  phase: string;
  technique_id: string;
  question: string;
}): Promise<DoubtAnswerResponse> {
  const response = await apiClient.post("/support/doubt/ask", payload);
  return response.data;
}

export async function fetchSupportResources(params: {
  skill_id: string;
  phase: string;
  query?: string;
}): Promise<SupportResourcesResponse> {
  const response = await apiClient.get("/support/resources", {
    params,
  });
  return response.data;
}

export async function fetchTip(sessionId: string): Promise<TipResponse> {
  const response = await apiClient.get(`/tip/${sessionId}`);
  return response.data;
}
