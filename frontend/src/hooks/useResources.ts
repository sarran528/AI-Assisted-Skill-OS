import { useQuery } from "@tanstack/react-query";

import { fetchSupportResources } from "../api/support";

export function useResources(skillId: string, phase: string, techniqueId?: string) {
  return useQuery({
    queryKey: ["support-resources", skillId, phase, techniqueId],
    queryFn: () => fetchSupportResources({ skill_id: skillId, phase, technique_id: techniqueId }),
    enabled: Boolean(skillId && phase),
    staleTime: 45_000,
  });
}
