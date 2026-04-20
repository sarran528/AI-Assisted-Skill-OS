import { apiClient } from "./client";
import type { GroundingPayload, SkillItem } from "../types";

export async function getSkills(): Promise<SkillItem[]> {
  const response = await apiClient.get("/skills");
  return response.data;
}

export async function submitGrounding(payload: GroundingPayload): Promise<unknown> {
  const response = await apiClient.post("/skills/baseline", payload);
  return response.data;
}
