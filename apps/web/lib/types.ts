export interface Judgment {
  id: string;
  decision_id: string;
  judge_name: string;
  disposition: string;
  reasoning: string;
  confidence: number;
  value: Record<string, unknown>;
  created_at: string;
}

export interface Decision {
  id: string;
  action_type: string;
  disposition: string;
  agent: string;
  environment: string;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  judgments: Judgment[];
  policy_trace: string[];
  outcome: Record<string, unknown> | null;
  latency_ms: number;
  created_at: string;
  updated_at: string;
}

export interface Review {
  id: string;
  decision_id: string;
  reviewer: string | null;
  status: "pending" | "approved" | "rejected";
  reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface PolicyVersion {
  id: string;
  policy_id: string;
  version: number;
  content: string;
  changelog: string;
  created_at: string;
}

export interface Policy {
  id: string;
  name: string;
  description: string;
  action_types: string[];
  active_version: number;
  versions: PolicyVersion[];
  created_at: string;
  updated_at: string;
}

export interface ReplayRun {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed";
  total_decisions: number;
  processed_decisions: number;
  matches: number;
  mismatches: number;
  errors: number;
  created_at: string;
  completed_at: string | null;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  actor: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface AnalyticsOverview {
  total_decisions: number;
  disposition_breakdown: Record<string, number>;
  pending_reviews: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  decisions_today: number;
  decisions_this_week: number;
}
