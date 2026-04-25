import { useMutation, useQuery } from "@tanstack/react-query";
import { generateRoadmap, getRoadmap, getRoadmapStatus } from "../api/roadmap";

export function useRoadmap(userId: string | undefined, skillId: string | undefined) {
  const { data: roadmap, error } = useQuery({
    queryKey: ["roadmap", userId],
    queryFn: () => getRoadmap(userId!),
    enabled: !!userId,
  });

  const { mutate: generateRoadmapMutate } = useMutation({
    mutationFn: (payload: { userId: string; skillId: string }) => generateRoadmap({ skill_id: payload.skillId }),
  });

  const { mutate: getRoadmapStatusMutate } = useMutation({
    mutationFn: (userId: string) => getRoadmapStatus(userId),
  });

  return {
    roadmap,
    error,
    generateRoadmap: generateRoadmapMutate,
    getRoadmapStatus: getRoadmapStatusMutate,
  };
}
