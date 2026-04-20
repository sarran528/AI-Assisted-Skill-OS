export interface AuthUser {
  userId: string;
  email: string;
}

export interface AuthResponse {
  accessToken: string;
  tokenType: string;
  userId?: string;
  email?: string;
}

export interface AssessmentMetrics {
  mean_response_time: number;
  response_time_variance: number;
  performance_decay: number;
  retry_depth: number;
  accuracy: number;
}

export interface AssessmentStartResponse {
  session_id: string;
  levels: number[];
}

export interface LevelSubmissionPayload {
  level: number;
  metrics: {
    accuracy: number;
    expected_time: number;
    latency_stability: number;
    decay_inverse: number;
    dropout: number;
    retry: number;
    recovery: number;
  };
  time_constraint: {
    available_hours_per_week: number;
    preferred_session_length: number;
  };
}

export interface SkillItem {
  id?: string;
  skill_id: string;
  name: string;
  domain?: string;
}

export interface GroundingPayload {
  skill_id: string;
  recognition: { items: boolean[] };
  familiarity: { answers: number[] };
  confidence: { level: number };
}

export interface RoadmapGenerateResponse {
  roadmap_id?: string;
  fingerprint?: string;
  job_id?: string;
  status: string;
}

export interface SessionStartResponse {
  session_id: string;
  status: string;
}

export interface SessionMetricsPayload {
  session_id: string;
  accuracy: number;
  elapsed_seconds: number;
  errors: number;
  retry: number;
}
