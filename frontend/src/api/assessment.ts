import axiosClient from "./axiosClient";
import type { AssessmentStartResponse, LevelSubmissionPayload } from "../types";

export async function startAssessment(): Promise<AssessmentStartResponse> {
  const response = await axiosClient.post("/assessment/start");
  return response.data;
}

export async function submitAssessmentLevel(payload: LevelSubmissionPayload): Promise<unknown> {
  const response = await axiosClient.post("/assessment/submit", payload);
  return response.data;
}

export async function completeAssessment(payload: {
  session_id: string;
  completed_levels: number[];
}): Promise<unknown> {
  const response = await axiosClient.post("/assessment/complete", payload);
  return response.data;
}
