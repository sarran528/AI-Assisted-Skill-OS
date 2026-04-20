import { useQuery } from "@tanstack/react-query";

import { fetchSupportResources } from "../api/support";

export function useResources(skillId: string, phase: string, query?: string) {
  return useQuery({
    queryKey: ["support-resources", skillId, phase, query],
    queryFn: () => fetchSupportResources({ skill_id: skillId, phase, query }),
    enabled: Boolean(skillId && phase),
    staleTime: 45_000,
  });
}
