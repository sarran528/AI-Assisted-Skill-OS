import axiosClient from "./axiosClient";
import type {
  DoubtAnswerResponse,
  SupportResourcesResponse,
  TipResponse,
} from "../types";

export async function askDoubt(payload: {
  session_id?: string | null;
  phase?: string | null;
  technique_id?: string | null;
  user_query: string;
}): Promise<DoubtAnswerResponse> {
  const response = await axiosClient.post("/doubt/ask", payload);
  return response.data;
}

export async function fetchSupportResources(params: {
  skill_id: string;
  phase: string;
  technique_id?: string;
  user_query?: string;
}): Promise<SupportResourcesResponse> {
  const response = await axiosClient.get("/resources", {
    params,
  });
  return response.data;
}

export async function fetchTip(sessionId: string): Promise<TipResponse> {
  const response = await axiosClient.get(`/tip/${sessionId}`);
  return response.data;
}
