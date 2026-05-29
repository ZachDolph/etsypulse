import { useEffect, useState } from 'react';

import { getHealth, type HealthResponse } from './api';
import './styles.css';

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHealth()
      .then((result) => {
        setHealth(result);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Unable to reach backend');
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">EtsyPulse Session 0</p>
        <h1>Autonomous Etsy market intelligence, starting with a clean demo shell.</h1>
        <p className="lede">
          This placeholder dashboard proves the React frontend can reach the FastAPI backend before agents, Bright Data, or LLM calls are added.
        </p>
      </section>

      <section className="status-card" aria-live="polite">
        <div>
          <p className="label">Backend health</p>
          {loading && <p className="status muted">Checking /health...</p>}
          {error && <p className="status error">{error}</p>}
          {health && (
            <div className="health-grid">
              <span>Status</span>
              <strong>{health.status}</strong>
              <span>Service</span>
              <strong>{health.service}</strong>
              <span>Demo mode</span>
              <strong>{health.demo_mode ? 'Enabled' : 'Disabled'}</strong>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

export default App;
