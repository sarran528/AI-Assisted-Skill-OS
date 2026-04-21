import { useMutation } from "@tanstack/react-query";

import { uploadEvidence } from "../api/evidence";
import { completeSession, startSession, submitSessionMetrics } from "../api/session";
import { validateCheckpoint } from "../api/validation";
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
