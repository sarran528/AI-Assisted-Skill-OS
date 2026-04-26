import { useMutation, useQuery } from "@tanstack/react-query";

import { completeAssessment, startAssessment, submitAssessmentLevel, getAssessmentStatus } from "../api/assessment";
import type { LevelSubmissionPayload } from "../types";

export function useStartAssessment() {
  return useMutation({ mutationFn: () => startAssessment() });
}

export function useSubmitLevel() {
  return useMutation({ mutationFn: (payload: LevelSubmissionPayload) => submitAssessmentLevel(payload) });
}

export function useCompleteAssessment() {
  return useMutation({
    mutationFn: (payload: { session_id: string }) => completeAssessment(payload),
  });
}

export function useAssessmentStatus() {
  return useQuery({
    queryKey: ["assessmentStatus"],
    queryFn: () => getAssessmentStatus(),
  });
}
