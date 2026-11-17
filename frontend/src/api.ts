import { AnalyticsResponse, RequestLogItem, ChatCompletionResult } from './types';

export async function fetchAnalytics(): Promise<AnalyticsResponse> {
  const res = await fetch('/api/analytics');
  if (!res.ok) throw new Error('Failed to load gateway analytics');
  return res.json();
}

export async function fetchLogs(limit = 50): Promise<RequestLogItem[]> {
  const res = await fetch(`/api/logs?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to load request logs');
  const data = await res.json();
  return data.logs;
}

export async function fetchConfig(): Promise<Record<string, any>> {
  const res = await fetch('/api/config');
  if (!res.ok) throw new Error('Failed to load gateway configuration');
  return res.json();
}

export async function clearCache(): Promise<void> {
  await fetch('/api/cache/clear', { method: 'POST' });
}

export async function sendGatewayCompletion(params: {
  prompt: string;
  strategy: 'complexity' | 'cost' | 'balanced';
  useCache: boolean;
  cacheThreshold: number;
  simulateFailure: boolean;
}): Promise<ChatCompletionResult> {
  const res = await fetch('/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'auto',
      messages: [{ role: 'user', content: params.prompt }],
      routing_strategy: params.strategy,
      use_cache: params.useCache,
      cache_threshold: params.cacheThreshold,
      simulate_failure: params.simulateFailure,
    }),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(errText || 'Gateway request failed');
  }
  return res.json();
}
