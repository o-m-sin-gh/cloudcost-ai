export interface Connection {
  connected: boolean; mode: "demo" | "aws"; account_id: string; arn: string; region: string;
  last_successful_connection: string; previous_successful_connection: string | null;
  writes_enabled: boolean; managed_prefix: string;
}
export interface LambdaFn {
  name: string; arn: string; runtime: string; memory_mb: number; timeout_s: number; architecture: string;
  last_modified: string; state: string; last_update_status: string; managed: boolean;
}
export interface Inventory { meta: { account_id: string; region: string; mode: string; fetched_at: string; count: number }; functions: LambdaFn[] }
export interface SeriesPoint { ts: string; invocations: number; avg_duration_ms: number; max_duration_ms: number; errors: number }
export interface Metrics {
  function: string; source: string; period_days: number; invocations: number; errors: number; throttles: number;
  avg_duration_ms: number; max_duration_ms: number; max_concurrent: number; series: SeriesPoint[];
  max_memory_used_mb: number | null; memory_utilization_pct: number | null;
  summary: { status: string; error_rate_pct: number };
}
export interface Analysis {
  function_name: string; current_memory_mb: number; recommended_memory_mb: number | null; finding: string;
  status: "optimized" | "opportunity" | "increase_suggested" | "awaiting_data";
  reason_codes: string[]; source: string | null; current_monthly_cost: number; recommended_monthly_cost: number | null;
  monthly_savings: number | null; annual_savings: number | null; savings_source: "aws" | "estimated" | "none";
  savings_per_million_invocations: number | null; performance_risk: number | null; eligible: boolean;
  rule_notes: string[]; explanation: string; action: string; data_source: string; managed: boolean;
  invocations: number; avg_duration_ms: number; max_memory_used_mb: number | null; architecture: string;
}
export interface Recommendations {
  generated_at: string; optimizer: { status: string; message: string }; items: Analysis[];
  summary: {
    total_functions: number; analysed: number; opportunities: number; opportunities_out_of_scope: number;
    potential_monthly_savings: number; potential_annual_savings: number; savings_at_1m_invocations: number;
    data_source: string; savings_label: string;
  };
}
export interface CostRow {
  function_name: string; current_memory_mb: number; recommended_memory_mb: number | null; current_monthly_cost: number;
  recommended_monthly_cost: number | null; monthly_savings: number | null; annual_savings: number | null;
  savings_source: string; savings_per_million_invocations: number | null; status: string; eligible: boolean;
}
export interface CostAnalysis { summary: Recommendations["summary"]; rows: CostRow[]; disclaimer: string }
export interface Verification {
  verdict: string; message: string; checked_at?: string; data_source?: string;
  avg_duration_ms?: { before: number; after: number; change_pct: number | null };
  cost_per_1000_invocations?: { before: number; after: number; change_pct: number | null };
}
export interface OptRecord {
  id: string; created_at: string; status: "previewed" | "approved" | "rejected" | "applied" | "failed" | "rolled_back";
  account_id: string; region: string; mode: string; function_name: string; old_memory_mb: number;
  target_memory_mb: number; new_memory_mb: number | null; recommendation_source: string | null;
  estimated_monthly_savings: number | null; savings_source: string | null; approved_at: string | null;
  applied_at: string | null; error: string | null; verification: Verification | null; rule_notes: string[];
  dry_run: { aws_calls_that_would_run: string[]; note: string }; rollback: { rolled_back_at: string } | null;
}
export interface ReportFile { name: string; exists: boolean; size_bytes: number }
export interface AppSettings {
  mode: string; region: string; lookback_days: number; min_monthly_savings_usd: number; allow_writes: boolean;
  managed_prefix: string; max_reduction_pct: number;
}
