import { useMutation } from "@tanstack/react-query";

import { startSession, submitSessionMetrics } from "../api/session";
import type { SessionMetricsPayload } from "../types";

export function useStartSession() {
  return useMutation({
    mutationFn: (payload: { skill_id: string; phase: string; technique_id: string }) => startSession(payload),
  });
}

export function useSubmitSessionMetrics() {
  return useMutation({
    mutationFn: (payload: SessionMetricsPayload) => submitSessionMetrics(payload),
  });
}
