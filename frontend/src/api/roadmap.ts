import { apiClient } from "./client";
import type { Roadmap, RoadmapGenerateRequest, RoadmapGenerateResponse } from "../types";

export async function getRoadmap(skillId: string): Promise<Roadmap> {
  const response = await apiClient.get(`/roadmap/${skillId}`);
  return response.data;
}

export async function generateRoadmap(payload: RoadmapGenerateRequest): Promise<RoadmapGenerateResponse> {
  const response = await apiClient.post("/roadmap/generate", payload);
  return response.data;
}

export async function getRoadmapStatus(jobId: string): Promise<{ status: string }> {
  const response = await apiClient.get(`/roadmap/status/${jobId}`);
  return response.data;
}
