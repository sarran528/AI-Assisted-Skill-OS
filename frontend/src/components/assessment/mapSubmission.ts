import type { LevelSubmissionPayload } from "../../types";

/** Maps cognitive task output (0–1 accuracy) to API submission fields. */
export function mapTaskResultsToSubmission(
  sessionId: string,
  level: number,
  taskMetrics: {
    accuracy?: number;
    mean_response_time?: number;
    response_time_variance?: number;
    performance_decay?: number;
    retry_depth?: number;
    dropout_depth_index?: number;
    recovery_slope?: number;
    raw?: Record<string, unknown>;
  }
): LevelSubmissionPayload {
  const acc = typeof taskMetrics.accuracy === "number" ? taskMetrics.accuracy : 0;
  const accuracyPct = acc <= 1 ? Math.round(acc * 100) : Math.round(acc);
  const meanRt = taskMetrics.mean_response_time ?? 0;
  const rtVar = taskMetrics.response_time_variance ?? 0;
  const decay = taskMetrics.performance_decay ?? 0;
  const retry = taskMetrics.retry_depth ?? 0;
  const dropout = taskMetrics.dropout_depth_index ?? 0;
  const recovery = taskMetrics.recovery_slope ?? 0;

  const raw = taskMetrics.raw ?? {};
  const available =
    typeof raw.available_hours_per_week === "number"
      ? Math.round(raw.available_hours_per_week as number)
      : 8;
  const sessionLen =
    typeof raw.preferred_session_length === "number"
      ? Math.round(raw.preferred_session_length as number)
      : 45;

  return {
    session_id: sessionId,
    level,
    metrics: {
      accuracy: accuracyPct,
      expected_time: Math.max(1, meanRt / 1000),
      latency_stability: Math.min(25, rtVar / 10000),
      decay_inverse: Math.max(0, 1 - decay),
      dropout: Math.min(3, Math.max(0, dropout)),
      retry: Math.min(1, Math.max(0, retry)),
      recovery: Math.min(1, Math.max(0, recovery)),
    },
    time_constraint: {
      available_hours_per_week: available,
      preferred_session_length: Math.min(240, Math.max(15, sessionLen)),
    },
  };
}
