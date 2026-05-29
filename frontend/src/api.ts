export type HealthResponse = {
  status: 'ok';
  service: string;
  demo_mode: boolean;
};

export type EvidenceSource = {
  tool: string;
  url?: string | null;
  title?: string | null;
  captured_at: string;
};

export type Listing = {
  id: string;
  shop_id: string;
  title: string;
  url: string;
  price: number;
  currency: string;
  tags: string[];
  provenance: EvidenceSource[];
  confidence: number;
  timestamp: string;
};

export type ShopProfile = {
  id: string;
  shop_url: string;
  shop_name: string;
  category: string;
  summary: string;
  listings: Listing[];
  seed_keywords: string[];
  likely_competitors: string[];
  baseline_positioning: string;
  provenance: EvidenceSource[];
  confidence: number;
  timestamp: string;
};

export type Severity = 'low' | 'medium' | 'high';
export type Decision = 'ignore' | 'watch' | 'brief';

export type KeywordSignal = {
  id: string;
  run_id: string;
  keyword: string;
  movement: string;
  opportunity: string;
  visibility_score: number;
  severity: Severity;
  provenance: EvidenceSource[];
  confidence: number;
  timestamp: string;
};

export type CompetitorSignal = {
  id: string;
  run_id: string;
  competitor_name: string;
  competitor_url: string;
  signal: string;
  price_delta_percent?: number | null;
  severity: Severity;
  provenance: EvidenceSource[];
  confidence: number;
  timestamp: string;
};

export type TrendSignal = {
  id: string;
  run_id: string;
  platform: string;
  topic: string;
  signal: string;
  momentum_score: number;
  severity: Severity;
  provenance: EvidenceSource[];
  confidence: number;
  timestamp: string;
};

export type MarketPulseSignal = {
  id: string;
  run_id: string;
  title: string;
  summary: string;
  severity: Severity;
  novelty: number;
  confidence: number;
  source_signal_ids: string[];
  provenance: EvidenceSource[];
  originating_agent: string;
  timestamp: string;
};

export type JudgeScore = {
  id: string;
  run_id: string;
  market_pulse_signal_id: string;
  actionability: number;
  urgency: number;
  confidence: number;
  novelty: number;
  business_impact: number;
  evidence_quality: number;
  total_score: number;
  decision: Decision;
  rationale: string;
  timestamp: string;
};

export type Brief = {
  id: string;
  run_id: string;
  shop_id: string;
  title: string;
  summary: string;
  recommended_actions: string[];
  evidence: string[];
  why_now: string;
  confidence: number;
  judge_score: JudgeScore;
  provenance: EvidenceSource[];
  timestamp: string;
};

export type AgentRun = {
  id: string;
  shop_id: string;
  mode: 'demo' | 'live';
  status: 'queued' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string | null;
  agents: string[];
  keyword_signals: KeywordSignal[];
  competitor_signals: CompetitorSignal[];
  trend_signals: TrendSignal[];
  market_pulse_signals: MarketPulseSignal[];
  judge_scores: JudgeScore[];
  brief_ids: string[];
};

export type ActivityEvent = {
  id: string;
  run_id?: string | null;
  agent: string;
  event_type: string;
  message: string;
  severity: 'info' | 'warning' | 'error';
  timestamp: string;
};

export type DebugEvent = {
  id: string;
  run_id?: string | null;
  provider: string;
  tool_name?: string | null;
  model?: string | null;
  operation: string;
  status: 'stubbed' | 'success' | 'error';
  cache_mode: 'demo' | 'live';
  latency_ms: number;
  request_shape: Record<string, unknown>;
  token_counts: Record<string, number>;
  error_class?: string | null;
  fallback_used: boolean;
  request_summary: string;
  response_summary: string;
  redacted: boolean;
  timestamp: string;
};


export type ProviderStatus = {
  name: string;
  configured: boolean;
  mode: 'demo' | 'live' | 'hybrid';
  details: Record<string, unknown>;
};

export type AdminDebugStatus = {
  demo_mode: boolean;
  brightdata: ProviderStatus;
  nvidia_nim: ProviderStatus;
  openrouter: ProviderStatus;
  live_ready: boolean;
};

export type SchedulerStatus = {
  demo_enabled: boolean;
  intervals_minutes: Record<'keyword' | 'competitor' | 'trend', number>;
  judge_brief_threshold: number;
};

export type SchedulerTriggerResponse = {
  status: 'completed' | 'duplicate_suppressed';
  run: AgentRun | null;
  check_types: Array<'keyword' | 'competitor' | 'trend' | 'all'>;
  message: string;
  duplicate_suppressed: boolean;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? `${window.location.protocol}//${window.location.hostname}:8000`;

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${path} failed with ${response.status}${detail ? `: ${detail}` : ''}`);
  }

  return response.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>('/health');
}

export function bootstrapShop(shopUrl: string): Promise<ShopProfile> {
  return requestJson<ShopProfile>('/shops/bootstrap-request', {
    method: 'POST',
    body: JSON.stringify({ shop_url: shopUrl }),
  });
}

export function getShop(shopId: string): Promise<ShopProfile> {
  return requestJson<ShopProfile>(`/shops/${shopId}`);
}

export function getRun(runId: string): Promise<AgentRun> {
  return requestJson<AgentRun>(`/runs/${runId}`);
}

export function triggerScheduledRun(shopId?: string): Promise<SchedulerTriggerResponse> {
  return requestJson<SchedulerTriggerResponse>('/scheduler/trigger', {
    method: 'POST',
    body: JSON.stringify({ shop_id: shopId ?? null, check_type: 'all', mode: 'demo_scheduled' }),
  });
}

export function getSchedulerStatus(): Promise<SchedulerStatus> {
  return requestJson<SchedulerStatus>('/scheduler/status');
}

export function getActivity(): Promise<ActivityEvent[]> {
  return requestJson<ActivityEvent[]>('/activity');
}

export function getBriefs(): Promise<Brief[]> {
  return requestJson<Brief[]>('/briefs');
}

export function getDebugEvents(): Promise<DebugEvent[]> {
  return requestJson<DebugEvent[]>('/debug/events');
}

export function getAdminDebugStatus(): Promise<AdminDebugStatus> {
  return requestJson<AdminDebugStatus>('/admin/debug/status');
}
