import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';

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

const DEMO_SHOP_URL = 'https://www.etsy.com/shop/demo-linen-studio';

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

    setData({ health, scheduler, shop, run, briefs, activity, debugEvents, adminStatus });
  }, []);

  useEffect(() => {
    refreshDashboard()
      .catch((err: unknown) => setError(readError(err)))
      .finally(() => setLoading(false));
    const interval = window.setInterval(() => {
      refreshDashboard().catch((err: unknown) => setError(readError(err)));
    }, 15000);
    return () => window.clearInterval(interval);
  }, [refreshDashboard]);

  async function handleSetup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runDemo(shopUrl);
  }

  async function runDemo(url: string) {
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
          <p className="eyebrow">EtsyPulse autonomous market desk</p>
          <h1>Set the shop once. Agents watch the market. Only useful briefs land.</h1>
          <p className="lede">
            EtsyPulse turns cached Bright Data-style market evidence and deterministic agent scoring into a seller cockpit: shop context, live agent activity, market pulse signals, Judge scores, and actionable recommendations.
          </p>
          <div className="hero-actions">
            <button className="primary-action" disabled={running} onClick={() => runDemo(DEMO_SHOP_URL)}>
              {running ? 'Agents running...' : 'Run demo shop'}
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

      {error && <StatusNotice tone="error" title="Dashboard needs attention" message={error} />}
      {loading && <StatusNotice tone="neutral" title="Loading intelligence workspace" message="Fetching health, scheduler status, briefs, activity, and debug events from FastAPI." />}

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
            Use deterministic demo shop
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

function ShopCard({ shop }: { shop: ShopProfile | null }) {
  if (!shop) {
    return (
      <article className="shop-card empty-state">
        <p className="section-kicker">Shop profile</p>
        <h2>Waiting for a shop.</h2>
        <p>Use the demo shop to populate listings, seed keywords, competitor seeds, and baseline positioning.</p>
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
        <p>{shop.seed_keywords.join(' · ')}</p>
      </div>
      <div className="mini-list">
        <strong>Competitors</strong>
        <p>{shop.likely_competitors.join(' · ')}</p>
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
            <span>{percent(brief.judge_score.total_score)} total Judge score</span>
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
  return (
    <section className="panel compact-panel">
      <div className="panel-heading">
        <div>
          <p className="section-kicker">Live activity</p>
          <h2>Agent run states</h2>
        </div>
        <span className="pill">{run?.status ?? 'idle'}</span>
      </div>
      {activity.length === 0 && <EmptyPanel title="No activity yet" message="Agent milestones will stream here after setup." />}
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
