export interface KpiMetrics {
  total_requests: number;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_cost_usd: number;
  baseline_cost_usd: number;
  total_savings_usd: number;
  savings_percentage: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  cache_hits: number;
  cache_hit_rate: number;
  fallback_count: number;
}

export interface ModelBreakdown {
  model: string;
  provider: string;
  requests: number;
  tokens: number;
  cost_usd: number;
  avg_latency_ms: number;
}

export interface TimeSeriesPoint {
  time_bucket: string;
  requests: number;
  tokens: number;
  actual_cost: number;
  baseline_cost: number;
  avg_latency: number;
}

export interface ProviderHealth {
  provider: string;
  status: 'healthy' | 'degraded' | 'circuit_open';
  recent_failures: number;
  total_successes: number;
}

export interface CacheStats {
  entries_count: number;
  default_threshold: number;
  ttl_seconds: number;
  total_cache_hits: number;
}

export interface AnalyticsResponse {
  kpis: KpiMetrics;
  model_breakdown: ModelBreakdown[];
  timeseries: TimeSeriesPoint[];
  providers: ProviderHealth[];
  cache: CacheStats;
  sandbox_mode: boolean;
}

export interface TraceStep {
  step: string;
  status: 'hit' | 'miss' | 'routed' | 'failed' | 'recovered' | 'completed';
  detail: string;
  duration_ms: number;
}

export interface RequestLogItem {
  id: number;
  request_id: string;
  created_at: string;
  prompt_preview: string;
  routing_strategy: string;
  complexity_score: number;
  complexity_tier: string;
  selected_model: string;
  provider: string;
  cache_hit: boolean;
  cache_similarity: number | null;
  fallback_triggered: boolean;
  attempted_models: string[];
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  baseline_cost_usd: number;
  savings_usd: number;
  latency_ms: number;
  trace: TraceStep[];
}

export interface ChatCompletionResult {
  id: string;
  model: string;
  choices: {
    index: number;
    message: { role: string; content: string };
  }[];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  gateway: {
    request_id: string;
    routing_strategy: string;
    complexity_score: number;
    complexity_tier: string;
    selected_model: string;
    provider: string;
    cache_hit: boolean;
    cache_similarity: number | null;
    fallback_triggered: boolean;
    attempted_models: string[];
    latency_ms: number;
    cost_usd: number;
    baseline_cost_usd: number;
    savings_usd: number;
    sandbox_mode: boolean;
    trace: TraceStep[];
  };
}
