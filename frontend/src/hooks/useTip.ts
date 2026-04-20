import { useQuery } from "@tanstack/react-query";

import { fetchTip } from "../api/support";

export function useTip(sessionId: string | null, enabled = false) {
  return useQuery({
    queryKey: ["tip", sessionId],
    queryFn: () => fetchTip(sessionId as string),
    enabled: Boolean(sessionId) && enabled,
    refetchInterval: enabled ? 3_000 : false,
    retry: false,
  });
}
