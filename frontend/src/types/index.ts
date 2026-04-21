export interface AuthUser {
  userId: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id?: string;
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
  session_id: string;
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

export interface SessionListItem {
  session_id: string;
  status: string;
  phase: string;
  score: number | null;
  created_at?: string;
}

export interface SessionCompleteResponse {
  session_id: string;
  passed: boolean;
  tip_pending?: boolean;
  completed_steps: string[];
  failure_reason?: string;
}

export interface SessionMetricsPayload {
  session_id: string;
  accuracy: number;
  elapsed_seconds: number;
  errors: number;
  retry: number;
}

export interface EvidenceUploadResponse {
  evidence_id: string;
  session_id: string;
  checkpoint_id: string;
  artifact_url?: string;
  mime_type?: string;
  file_size_bytes: number;
  validated: boolean;
}

export interface CheckpointValidationResponse {
  passed: boolean;
  reason: string;
  session_id: string;
  checkpoint_id: string;
}

export interface DoubtAnswerResponse {
  answer: string;
  confidence: "low" | "medium" | "high";
  caveat?: string;
  sources_used?: number;
}

export interface SupportResourceItem {
  id: string;
  doc_type: string;
  snippet: string;
  relevance: number;
}

export interface SupportResourcesResponse {
  items: SupportResourceItem[];
}

export interface TipResponse {
  available: boolean;
  severity?: "minor" | "moderate" | "critical";
  text?: string;
  focus_step?: string;
}
