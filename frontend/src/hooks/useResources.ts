import { useQuery } from "@tanstack/react-query";

import { fetchSupportResources } from "../api/support";

export function useResources(skillId: string, phase: string, techniqueId?: string, userQuery?: string) {
  return useQuery({
    queryKey: ["support-resources", skillId, phase, techniqueId, userQuery],
    queryFn: () => fetchSupportResources({ skill_id: skillId, phase, technique_id: techniqueId, user_query: userQuery }),
    enabled: Boolean(skillId && phase),
    staleTime: 45_000,
  });
}
