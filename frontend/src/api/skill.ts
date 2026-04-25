import axiosClient from "./axiosClient";
import type { GroundingPayload, SkillItem } from "../types";

export async function getSkills(): Promise<SkillItem[]> {
  const response = await axiosClient.get<Array<{ skill_id: string; name: string; complexity_score: number }>>(
    "/skill/list"
  );
  return response.data.map((item) => ({
    skill_id: item.skill_id,
    name: item.name,
    domain: "",
  }));
}

export async function submitGrounding(payload: GroundingPayload): Promise<unknown> {
  const response = await axiosClient.post("/skill/baseline", payload);
  return response.data;
}
