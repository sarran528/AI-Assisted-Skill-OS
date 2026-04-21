import { useMutation, useQuery } from "@tanstack/react-query";
import { generateRoadmap, getRoadmap, getRoadmapStatus } from "../api/roadmap";

export function useRoadmap(skillId: string | undefined) {
  const { data: roadmap, error } = useQuery({
    queryKey: ["roadmap", skillId],
    queryFn: () => getRoadmap(skillId!),
    enabled: !!skillId,
  });

  const { mutate: generateRoadmapMutate } = useMutation({
    mutationFn: (skillId: string) => generateRoadmap({ skill_id: skillId }),
  });

  const { mutate: getRoadmapStatusMutate } = useMutation({
    mutationFn: (jobId: string) => getRoadmapStatus(jobId),
  });

  return {
    roadmap,
    error,
    generateRoadmap: generateRoadmapMutate,
    getRoadmapStatus: getRoadmapStatusMutate,
  };
}
