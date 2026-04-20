import { useMutation } from "@tanstack/react-query";

import { generateRoadmap } from "../api/roadmap";

export function useGenerateRoadmap() {
  return useMutation({
    mutationFn: (skillId: string) => generateRoadmap(skillId),
  });
}
