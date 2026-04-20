import { useMutation, useQuery } from "@tanstack/react-query";

import { getSkills, submitGrounding } from "../api/skill";
import type { GroundingPayload } from "../types";

export function useSkills() {
  return useQuery({
    queryKey: ["skills"],
    queryFn: getSkills,
    staleTime: 60_000,
  });
}

export function useSubmitGrounding() {
  return useMutation({
    mutationFn: (payload: GroundingPayload) => submitGrounding(payload),
  });
}
