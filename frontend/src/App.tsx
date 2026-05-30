import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react';

import {
  bootstrapShop,
  getActivity,
  getAdminDebugStatus,
  getBriefs,
  getDebugEvents,
  getHealth,
  getRun,
  getSchedulerStatus,
  getShop,
  triggerScheduledRun,
  type ActivityEvent,
  type AdminDebugStatus,
  type AgentRun,
  type Brief,
  type DebugEvent,
  type HealthResponse,
  type SchedulerStatus,
  type ShopProfile,
} from './api';
import './styles.css';

const DEMO_SHOP_URL = 'https://www.etsy.com/shop/CaitlynMinimalist';
const WAKEUP_MAX_RETRIES = 20;   // 20 × 8s = 160s — covers Render's worst cold starts
const WAKEUP_INTERVAL_MS = 8000;

type DashboardData = {
  health: HealthResponse | null;
  scheduler: SchedulerStatus | null;
  shop: ShopProfile | null;
  run: AgentRun | null;
  briefs: Brief[];
  activity: ActivityEvent[];
  debugEvents: DebugEvent[];
  adminStatus: AdminDebugStatus | null;
};

const emptyData: DashboardData = {
  health: null,
  scheduler: null,
  shop: null,
  run: null,
  briefs: [],
  activity: [],
  debugEvents: [],
  adminStatus: null,
};

function App() {
  const [data, setData] = useState<DashboardData>(emptyData);
  const [shopUrl, setShopUrl] = useState(DEMO_SHOP_URL);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wakeupAttempt, setWakeupAttempt] = useState(0);
  const [wakeupCountdown, setWakeupCountdown] = useState<number | null>(null);
  const hasConnectedRef = useRef(false);
  const wakeupTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const countdownTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearWakeupTimers = () => {
    if (wakeupTimerRef.current) clearTimeout(wakeupTimerRef.current);
    if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
    wakeupTimerRef.current = null;
    countdownTimerRef.current = null;
  };

  const refreshDashboard = useCallback(async () => {
    const [health, scheduler, briefs, activity, debugEvents, adminStatus] = await Promise.all([
      getHealth(),
      getSchedulerStatus(),
      getBriefs(),
      getActivity(),
      getDebugEvents(),
      getAdminDebugStatus(),
    ]);

    const newestBrief = briefs[0];
    let run: AgentRun | null = null;
    let shop: ShopProfile | null = null;

    if (newestBrief) {
      run = await getRun(newestBrief.run_id);
      shop = await getShop(newestBrief.shop_id);
    }

    hasConnectedRef.current = true;
    clearWakeupTimers();
    setWakeupAttempt(0);
    setWakeupCountdown(null);
    setError(null);
    setData({ health, scheduler, shop, run, briefs, activity, debugEvents, adminStatus });
  }, []);

  const scheduleWakeupRetry = useCallback(
    (attempt: number, retryFn: () => void) => {
      if (attempt >= WAKEUP_MAX_RETRIES) return;
      let remaining = Math.round(WAKEUP_INTERVAL_MS / 1000);
      setWakeupCountdown(remaining);
      countdownTimerRef.current = setInterval(() => {
        remaining -= 1;
        setWakeupCountdown(remaining > 0 ? remaining : null);
        if (remaining <= 0 && countdownTimerRef.current) {
          clearInterval(countdownTimerRef.current);
          countdownTimerRef.current = null;
        }
      }, 1000);
      wakeupTimerRef.current = setTimeout(retryFn, WAKEUP_INTERVAL_MS);
    },
    [],
  );

  useEffect(() => {
    let attempt = 0;

    function tryConnect() {
      refreshDashboard()
        .catch((err: unknown) => {
          if (hasConnectedRef.current) {
            setError(readError(err));
            return;
          }
          attempt += 1;
          setWakeupAttempt(attempt);
          if (attempt < WAKEUP_MAX_RETRIES) {
            scheduleWakeupRetry(attempt, tryConnect);
          } else {
            setError(readError(err));
          }
        })
        .finally(() => setLoading(false));
    }

    tryConnect();

    const interval = window.setInterval(() => {
      if (hasConnectedRef.current) {
        refreshDashboard().catch(() => {});
      }
    }, 15000);

    return () => {
      window.clearInterval(interval);
      clearWakeupTimers();
    };
  }, [refreshDashboard, scheduleWakeupRetry]);

  async function handleSetup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runDemo(shopUrl);
  }

  async function runDemo(url: string) {
    // If we've never connected, reload to restart the wakeup sequence instead of failing silently
    if (!hasConnectedRef.current) {
      window.location.reload();
      return;
    }
    setRunning(true);
    setError(null);
    try {
      const shop = await bootstrapShop(url);
      const result = await triggerScheduledRun(shop.id);
      const [briefs, activity, debugEvents, scheduler, health, adminStatus] = await Promise.all([
        getBriefs(),
        getActivity(),
        getDebugEvents(),
        getSchedulerStatus(),
        getHealth(),
        getAdminDebugStatus(),
      ]);
      setData({ health, scheduler, shop, run: result.run, briefs, activity, debugEvents, adminStatus });
    } catch (err: unknown) {
      setError(readError(err));
    } finally {
      setRunning(false);
    }
  }

  const brightDataEvents = data.debugEvents.filter((event) => event.provider.toLowerCase().includes('bright'));
  const llmEvents = data.debugEvents.filter((event) => event.provider.toLowerCase().includes('llm') || event.model);
  const latestBrief = data.briefs[0] ?? null;
  const storyStats = useMemo(
    () => [
      { label: 'Agents', value: data.run?.agents.length ?? 7, detail: 'specialists watching the market' },
      { label: 'Signals', value: signalCount(data.run), detail: 'keyword, competitor, and trend inputs' },
      { label: 'Briefs', value: data.briefs.length, detail: 'Judge-approved seller actions' },
    ],
    [data.run, data.briefs.length],
  );

  return (
    <main className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <section className="hero-panel reveal">
        <div className="hero-copy">
          <div className="wordmark">
            <span className="wordmark-badge">EP</span>
            <span className="wordmark-text">EtsyPulse</span>
          </div>
          <h1>Set the shop once. Agents watch the market. Only useful briefs land.</h1>
          <p className="lede">
            Your competitors just changed their pricing. A TikTok trend is driving searches in your niche. Your SERP rank shifted overnight. Seven agents monitor all of it — keyword, competitor, and social signals — then a Judge Agent filters for what's actually worth acting on. You get a brief, not a dashboard.
          </p>
          <div className="hero-actions">
            <button className="primary-action" disabled={running} onClick={() => runDemo(DEMO_SHOP_URL)}>
              {running ? 'Agents running...' : 'Run CaitlynMinimalist demo'}
            </button>
            <a className="ghost-link" href="#briefs">View approved briefs</a>
          </div>
        </div>
        <div className="signal-card" aria-label="Demo status">
          <DemoBanner health={data.health} loading={loading} />
          <div className="radar">
            <span />
            <span />
            <span />
          </div>
          <p className="signal-title">Monitoring cadence</p>
          <p className="signal-copy">Keyword {data.scheduler?.intervals_minutes.keyword ?? '...'}m · Competitor {data.scheduler?.intervals_minutes.competitor ?? '...'}m · Trend {data.scheduler?.intervals_minutes.trend ?? '...'}m</p>
        </div>
      </section>

      {wakeupAttempt > 0 && !error && (
        <WakeupNotice attempt={wakeupAttempt} maxAttempts={WAKEUP_MAX_RETRIES} countdown={wakeupCountdown} />
      )}
      {error && (
        <BackendErrorNotice
          message={error}
          timedOut={wakeupAttempt >= WAKEUP_MAX_RETRIES}
          onRetry={() => window.location.reload()}
        />
      )}
      {loading && wakeupAttempt === 0 && !error && <StatusNotice tone="neutral" title="Loading intelligence workspace" message="Fetching health, scheduler status, briefs, activity, and debug events from FastAPI." />}

      <section className="setup-grid reveal delay-one">
        <form className="setup-card" onSubmit={handleSetup}>
          <p className="section-kicker">Shop setup</p>
          <h2>One input starts the loop.</h2>
          <label htmlFor="shop-url">Etsy shop URL</label>
          <div className="input-row">
            <input id="shop-url" value={shopUrl} onChange={(event) => setShopUrl(event.target.value)} placeholder="https://www.etsy.com/shop/your-shop" />
            <button disabled={running}>{running ? 'Monitoring...' : 'Monitor'}</button>
          </div>
          <button className="secondary-action" type="button" disabled={running} onClick={() => runDemo(DEMO_SHOP_URL)}>
            Use CaitlynMinimalist demo
          </button>
        </form>

        <ShopCard shop={data.shop} />
      </section>

      <section className="metric-strip reveal delay-two" aria-label="System summary">
        {storyStats.map((stat) => (
          <article key={stat.label} className="metric-card">
            <strong>{stat.value}</strong>
            <span>{stat.label}</span>
            <p>{stat.detail}</p>
          </article>
        ))}
      </section>

      <WorkflowRibbon />

      <section className="dashboard-grid reveal delay-three">
        <div className="main-column">
          <BriefsPanel briefs={data.briefs} latestBrief={latestBrief} />
          <MarketPulsePanel run={data.run} />
        </div>
        <aside className="side-column">
          <ActivityFeed activity={data.activity} run={data.run} />
          <ProviderStatusPanel adminStatus={data.adminStatus} />
          <DebugPanel debugEvents={data.debugEvents} brightDataCount={brightDataEvents.length} llmCount={llmEvents.length} />
        </aside>
      </section>
    </main>
  );
}

function WorkflowRibbon() {
  const steps = [
    { label: 'Shop URL', detail: 'bootstrap profile', tone: 'source' },
    { label: 'Bright Data', detail: 'collect web signals', tone: 'data' },
    { label: 'Agents', detail: 'normalize market pulse', tone: 'agent' },
    { label: 'Judge', detail: 'filter for actionability', tone: 'judge' },
    { label: 'Brief', detail: 'ship seller action', tone: 'brief' },
  ];
  return (
    <section className="workflow-ribbon reveal delay-two" aria-label="EtsyPulse workflow">
      {steps.map((step, index) => (
        <article className={`workflow-step ${step.tone}`} key={step.label}>
          <span>{String(index + 1).padStart(2, '0')}</span>
          <strong>{step.label}</strong>
          <p>{step.detail}</p>
        </article>
      ))}
    </section>
  );
}

function DemoBanner({ health, loading }: { health: HealthResponse | null; loading: boolean }) {
  if (loading) return <div className="demo-banner muted-banner">Checking demo mode</div>;
  return <div className="demo-banner">{health?.demo_mode ? 'Demo mode: no credentials required' : 'Live mode enabled'}</div>;
}

function StatusNotice({ tone, title, message }: { tone: 'neutral' | 'error'; title: string; message: string }) {
  return (
    <section className={`notice ${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <strong>{title}</strong>
      <span>{message}</span>
    </section>
  );
}

function WakeupNotice({ attempt, maxAttempts, countdown }: { attempt: number; maxAttempts: number; countdown: number | null }) {
  const apiUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? `${window.location.protocol}//${window.location.hostname}:8000`;
  return (
    <section className="notice wakeup" role="status" aria-live="polite">
      <div className="wakeup-row">
        <span className="wakeup-spinner" aria-hidden="true" />
        <strong>Backend is starting up — this takes up to 60 seconds on first load.</strong>
      </div>
      <span>
        Connecting to <code>{apiUrl}</code> · attempt {attempt}/{maxAttempts}
        {countdown !== null ? ` · retrying in ${countdown}s` : ' · retrying…'}
      </span>
    </section>
  );
}

function BackendErrorNotice({ message, timedOut, onRetry }: { message: string; timedOut: boolean; onRetry: () => void }) {
  const apiUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? `${window.location.protocol}//${window.location.hostname}:8000`;
  return (
    <section className="notice error" role="alert">
      <strong>{timedOut ? 'Backend is taking longer than expected to start.' : 'Cannot reach the EtsyPulse backend.'}</strong>
      <span>
        {timedOut
          ? 'The Render free-tier backend may need up to 90 seconds on a cold start. Click retry to try again — it usually connects on the second attempt.'
          : <>Tried <code>{apiUrl}</code> — {message}. The hosted backend may be offline.</>
        }
      </span>
      <div className="notice-actions">
        <button className="retry-btn" onClick={onRetry}>{timedOut ? 'Try again' : 'Retry'}</button>
        <span className="notice-hint">
          To run locally: <code>uvicorn app.main:app --port 8000</code> then set{' '}
          <code>VITE_API_BASE_URL=http://localhost:8000</code>
        </span>
      </div>
    </section>
  );
}

function ShopCard({ shop }: { shop: ShopProfile | null }) {
  if (!shop) {
    return (
      <article className="shop-card empty-state">
        <p className="section-kicker">Shop profile</p>
        <h2>Waiting for a shop.</h2>
        <p>Use the CaitlynMinimalist demo to populate listings, seed keywords, competitor seeds, and baseline positioning.</p>
      </article>
    );
  }

  return (
    <article className="shop-card">
      <p className="section-kicker">Shop profile</p>
      <h2>{shop.shop_name}</h2>
      <p>{shop.summary}</p>
      <div className="tag-row">
        <span>{shop.category}</span>
        <span>{percent(shop.confidence)} confidence</span>
      </div>
      <div className="mini-list">
        <strong>Seed keywords</strong>
        <div className="competitor-pills">
          {shop.seed_keywords.map((kw) => (
            <span key={kw} className="competitor-pill">{kw}</span>
          ))}
        </div>
      </div>
      <div className="mini-list">
        <strong>Competitors</strong>
        <div className="competitor-pills">
          {shop.likely_competitors.map((name) => (
            <span key={name} className="competitor-pill">{name}</span>
          ))}
        </div>
      </div>
    </article>
  );
}

function BriefsPanel({ briefs, latestBrief }: { briefs: Brief[]; latestBrief: Brief | null }) {
  return (
    <section className="panel" id="briefs">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">Actionable briefs</p>
          <h2>Judge-approved moves</h2>
        </div>
        <span className="pill">{briefs.length} approved</span>
      </div>

      {!latestBrief && <EmptyPanel title="No briefs yet" message="Run the demo shop to let agents gather signals and the Judge Agent approve only actionable opportunities." />}

      {briefs.slice(0, 3).map((brief) => (
        <article className="brief-card" key={brief.id}>
          <div className="brief-topline">
            <span className="decision">{brief.judge_score.decision}</span>
            <span className="judge-badge">Judge Agent · {percent(brief.judge_score.total_score)} total</span>
          </div>
          <h3>{brief.title}</h3>
          <p>{brief.summary}</p>
          <div className="score-grid">
            <Score label="Action" value={brief.judge_score.actionability} />
            <Score label="Urgency" value={brief.judge_score.urgency} />
            <Score label="Novelty" value={brief.judge_score.novelty} />
            <Score label="Impact" value={brief.judge_score.business_impact} />
            <Score label="Evidence" value={brief.judge_score.evidence_quality} />
            <Score label="Confidence" value={brief.judge_score.confidence} />
          </div>
          <div className="action-list">
            <strong>Recommended actions</strong>
            <ul>
              {brief.recommended_actions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          </div>
          <blockquote>{brief.why_now}</blockquote>
        </article>
      ))}
    </section>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div className="score-item">
      <span>{label}</span>
      <div className="score-bar"><i style={{ width: `${Math.round(value * 100)}%` }} /></div>
      <strong>{percent(value)}</strong>
    </div>
  );
}

function MarketPulsePanel({ run }: { run: AgentRun | null }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">Market pulse</p>
          <h2>Signals behind the brief</h2>
        </div>
        <span className="pill">{run?.status ?? 'idle'}</span>
      </div>
      {!run && <EmptyPanel title="No run selected" message="After a demo run, keyword, competitor, trend, and normalized market pulse signals appear here." />}
      {run && (
        <div className="pulse-grid">
          <SignalColumn title="Keywords" items={run.keyword_signals.map((signal) => ({ title: signal.keyword, body: signal.opportunity, metric: percent(signal.visibility_score) }))} />
          <SignalColumn title="Competitors" items={run.competitor_signals.map((signal) => ({ title: signal.competitor_name, body: signal.signal, metric: signal.price_delta_percent == null ? signal.severity : `${signal.price_delta_percent}%` }))} />
          <SignalColumn title="Social trends" items={run.trend_signals.map((signal) => ({ title: `${signal.platform}: ${signal.topic}`, body: signal.signal, metric: percent(signal.momentum_score) }))} />
          <SignalColumn title="Pulse events" items={run.market_pulse_signals.map((signal) => ({ title: signal.title, body: signal.summary, metric: signal.severity }))} />
        </div>
      )}
    </section>
  );
}

function SignalColumn({ title, items }: { title: string; items: Array<{ title: string; body: string; metric: string }> }) {
  return (
    <div className="signal-column">
      <h3>{title}</h3>
      {items.length === 0 && <p className="muted-copy">No signals yet.</p>}
      {items.slice(0, 4).map((item) => (
        <article key={`${title}-${item.title}`}>
          <span>{item.metric}</span>
          <strong>{item.title}</strong>
          <p>{item.body}</p>
        </article>
      ))}
    </div>
  );
}

function ActivityFeed({ activity, run }: { activity: ActivityEvent[]; run: AgentRun | null }) {
  const agentNames = run?.agents ?? [];
  return (
    <section className="panel compact-panel">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">Live activity</p>
          <h2>Agent activity</h2>
        </div>
        <span className="pill">{run?.status ?? 'idle'}</span>
      </div>
      {activity.length === 0 && <EmptyPanel title="No activity yet" message="Agent milestones will stream here after setup." />}
      {agentNames.length > 0 && (
        <div className="agent-strip" aria-label="Agent roster">
          {agentNames.map((agent) => (
            <span key={agent}>{agent.replace(' Agent', '')}</span>
          ))}
        </div>
      )}
      <div className="timeline">
        {activity.slice(0, 10).map((event) => (
          <article key={event.id}>
            <span className={`dot ${event.severity}`} />
            <div>
              <strong>{event.agent}</strong>
              <p>{event.message}</p>
              <time>{formatTime(event.timestamp)}</time>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}


function ProviderStatusPanel({ adminStatus }: { adminStatus: AdminDebugStatus | null }) {
  const providers = adminStatus ? [adminStatus.brightdata, adminStatus.nvidia_nim, adminStatus.openrouter] : [];
  return (
    <section className="panel compact-panel provider-panel">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">Live readiness</p>
          <h2>Provider status</h2>
        </div>
        <span className="pill">{adminStatus?.live_ready ? 'live ready' : 'demo safe'}</span>
      </div>
      {providers.length === 0 && <EmptyPanel title="Checking providers" message="Provider configuration appears here without exposing credentials." />}
      <div className="provider-list">
        {providers.map((provider) => (
          <article key={provider.name}>
            <span className={provider.configured ? 'status-dot ready' : 'status-dot missing'} />
            <div>
              <strong>{provider.name}</strong>
              <p>{provider.configured ? 'configured' : 'not configured'} · {provider.mode} mode</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function DebugPanel({ debugEvents, brightDataCount, llmCount }: { debugEvents: DebugEvent[]; brightDataCount: number; llmCount: number }) {
  const brightDataEvents = debugEvents.filter((event) => event.provider.toLowerCase().includes('bright'));
  return (
    <section className="panel compact-panel debug-panel">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">Debug trace</p>
          <h2>Provider evidence</h2>
        </div>
        <span className="pill">{brightDataCount} Bright Data · {llmCount} LLM</span>
      </div>
      {debugEvents.length === 0 && <EmptyPanel title="No debug events" message="Bright Data fixture loads and fake LLM scoring calls will appear here with redacted request shapes." />}
      {brightDataEvents.length > 0 && (
        <div className="brightdata-proof">
          <strong>Bright Data proof</strong>
          <p>{brightDataEvents.length} tool call traces · cache/live mode · latency · redacted requests</p>
        </div>
      )}
      <div className="debug-list">
        {debugEvents.slice(0, 8).map((event) => (
          <article key={event.id}>
            <div className="debug-topline">
              <strong>{event.provider}</strong>
              <span>{event.cache_mode} · {Math.round(event.latency_ms)}ms</span>
            </div>
            <p>{event.tool_name ?? event.model ?? event.operation}</p>
            <code>{safeJson(event.request_shape)}</code>
            <small>{event.redacted ? 'redacted' : 'not redacted'} · {event.response_summary}</small>
          </article>
        ))}
      </div>
    </section>
  );
}

function EmptyPanel({ title, message }: { title: string; message: string }) {
  return (
    <div className="empty-panel">
      <strong>{title}</strong>
      <p>{message}</p>
    </div>
  );
}

function signalCount(run: AgentRun | null): number {
  if (!run) return 0;
  return run.keyword_signals.length + run.competitor_signals.length + run.trend_signals.length + run.market_pulse_signals.length;
}

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit', month: 'short', day: 'numeric' }).format(new Date(value));
}

function safeJson(value: Record<string, unknown>): string {
  const text = JSON.stringify(value);
  return text.length > 92 ? `${text.slice(0, 92)}...` : text;
}

function readError(err: unknown): string {
  return err instanceof Error ? err.message : 'Unable to reach EtsyPulse backend';
}

export default App;
