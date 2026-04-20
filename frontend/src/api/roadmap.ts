import { apiClient } from "./client";
import type { RoadmapGenerateResponse } from "../types";

export async function generateRoadmap(skillId: string): Promise<RoadmapGenerateResponse> {
  const response = await apiClient.post("/roadmaps/generate", { skill_id: skillId });
  return response.data;
}
