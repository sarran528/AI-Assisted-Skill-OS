import axiosClient from "./axiosClient";
import type { Roadmap, RoadmapGenerateRequest, RoadmapGenerateResponse } from "../types";

export async function getRoadmap(userId: string): Promise<Roadmap> {
  const response = await axiosClient.get(`/roadmap/${userId}`);
  return response.data;
}

export async function generateRoadmap(payload: RoadmapGenerateRequest): Promise<RoadmapGenerateResponse> {
  const response = await axiosClient.post("roadmap/generate", payload);
  return response.data;
}

export async function getRoadmapStatus(userId: string): Promise<{ status: string }> {
  const response = await axiosClient.get(`/roadmap/${userId}/status`);
  return response.data;
}
