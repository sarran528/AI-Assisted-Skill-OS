import { useMutation, useQuery } from "@tanstack/react-query";

import { uploadEvidence } from "../api/evidence";
import {
  completeSession,
  getRecentSessions,
  getSession,
  startSession,
  submitSessionMetrics,
} from "../api/session";
import { validateCheckpoint } from "../api/validation";
import type { SessionMetricsPayload } from "../types";

export function useStartSession() {
  return useMutation({
    mutationFn: (payload: { skill_id: string; phase: string; technique_id: string }) => startSession(payload),
  });
}

export function useSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => getSession(sessionId!),
    enabled: !!sessionId,
  });
}

export function useRecentSessions(limit = 5) {
  return useQuery({
    queryKey: ["sessions", "recent", limit],
    queryFn: () => getRecentSessions(limit),
    staleTime: 30_000,
  });
}

export function useSubmitSessionMetrics() {
  return useMutation({
    mutationFn: (payload: SessionMetricsPayload) => submitSessionMetrics(payload),
  });
}

export function useCompleteSession() {
  return useMutation({
    mutationFn: (payload: { session_id: string; completed_steps: string[] }) => completeSession(payload),
  });
}

export function useUploadEvidence() {
  return useMutation({
    mutationFn: (payload: { sessionId: string; checkpointId: string; file: File; evidenceType?: string }) =>
      uploadEvidence(payload),
  });
}

export function useValidateCheckpoint() {
  return useMutation({
    mutationFn: (payload: { sessionId: string; checkpointId: string }) => validateCheckpoint(payload),
  });
}
