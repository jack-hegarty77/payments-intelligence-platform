import { useEffect, useState } from "react";
import { useRef } from "react";
import "./App.css";

function formatText(text) {
  return String(text)
    .replace(/[_-]+/g, " ")
    .split(" ")
    .filter(Boolean)
    .map(
      (word) =>
        word.charAt(0).toUpperCase() +
        word.slice(1)
    )
    .join(" ");
}
function getDisplayStatus(tx) {
  return tx.decision || tx.status || "APPROVED";
}

export default function App() {
  const [transactions, setTransactions] = useState([]);
  const [customerProfiles, setCustomerProfiles] = useState([]);
  const [selectedTransaction, setSelectedTransaction] =
    useState(null);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [selectedCustomerTxs, setSelectedCustomerTxs] = useState([]);
  const [connected, setConnected] = useState(false);
  const [statusMessage, setStatusMessage] =
    useState("Connecting to live feed...");
  const [errorMessage, setErrorMessage] = useState("");

  async function inspectCustomer(customer) {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/customers/${customer.customer_id}`
      );
      if (!response.ok) {
        throw new Error("Failed to load customer history");
      }

      const data = await response.json();
      setSelectedCustomer({ ...customer, profile: data.profile });
      setSelectedCustomerTxs(data.transactions || customer.txs || []);
    } catch {
      setSelectedCustomer(customer);
      setSelectedCustomerTxs(customer.txs || []);
    }
  }

  async function loadCustomerProfiles() {
    try {
      const response = await fetch("http://127.0.0.1:8000/customers");
      if (!response.ok) throw new Error("Failed to load customers");
      setCustomerProfiles(await response.json());
    } catch {
      setErrorMessage("Unable to load customer profiles.");
    }
  }

  useEffect(() => {
    async function loadInitial() {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/transactions/live"
        );
        if (!response.ok) {
          throw new Error("Failed to load live transactions");
        }

        const data = await response.json();
        setTransactions(data || []);
      } catch {
        setErrorMessage(
          "Unable to load recent transactions."
        );
      }
    }

    loadInitial();
    window.setTimeout(loadCustomerProfiles, 0);
    const profileRefresh = window.setInterval(loadCustomerProfiles, 2000);

    const socket = new WebSocket(
      "ws://127.0.0.1:8000/ws/transactions"
    );

    socket.onopen = () => {
      setConnected(true);
      setStatusMessage("Live stream connected");
      setErrorMessage("");
    };

    socket.onmessage = (event) => {
      const tx = JSON.parse(event.data);
      setTransactions((prev) => [...prev, tx].slice(-100));
    };

    socket.onerror = () => {
      setConnected(false);
      setStatusMessage("Live feed interrupted");
      setErrorMessage("WebSocket connection error.");
    };

    socket.onclose = () => {
      setConnected(false);
      setStatusMessage("Live feed disconnected");
    };

    return () => {
      socket.close();
      window.clearInterval(profileRefresh);
    };
  }, []);

  const recentTransactions = [...transactions].reverse();
  const latestTx = recentTransactions[0] || null;

  return (
    <div className="dashboard">
      <nav className="top-nav">
        <span className="nav-link active">Dashboard</span>
      </nav>
      <>
      <header className="header">
        <div className="header-row">
          <div>
            <h1>Payments Intelligence Platform</h1>
            <p className="subtitle">
              Real-time payment monitoring, risk alerts,
              and investigator tools in one dashboard.
            </p>
          </div>

          <div className="connection-panel">
            <span
              className={`connection-pill ${
                connected ? "connected" : "offline"
              }`}
            >
              <span className="pulse" />
              {connected ? "Live" : "Offline"}
            </span>
            <p className="connection-text">
              {statusMessage}
              {errorMessage ? ` • ${errorMessage}` : ""}
            </p>
          </div>
        </div>
      </header>

      <div className="simulated-time-bar">
        <div className="sim-time">
          {latestTx ? (
            <>
              Simulated time — Day {latestTx.simulation_day} · {latestTx.timestamp?.slice(11,16)}
            </>
          ) : (
            <>Simulated time — —</>
          )}
        </div>
      </div>

      <CustomerOverview profiles={customerProfiles} onInspect={inspectCustomer} />
        </>

      {selectedTransaction && (
        <div
          className="modal-overlay"
          onClick={() => setSelectedTransaction(null)}
        >
          <div
            className="modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="modal-header">
              <div>
                <h2>Transaction Investigation</h2>
                <p className="muted-text">
                  {selectedTransaction.transaction_id}
                </p>
              </div>
              <button
                className="close-button"
                onClick={() => setSelectedTransaction(null)}
              >
                Close
              </button>
            </div>

            <div className="modal-grid">
              <div>
                <p>
                  <strong>Merchant:</strong> {selectedTransaction.merchant}
                </p>
                <p>
                  <strong>Amount:</strong> €{selectedTransaction.amount.toFixed(2)}
                </p>
                <p>
                  <strong>Country:</strong> {selectedTransaction.country}
                </p>
                <p>
                  <strong>Status:</strong> {getDisplayStatus(selectedTransaction)}
                </p>
              </div>

              <div>
                <p>
                  <strong>Customer:</strong> {selectedTransaction.customer_id}
                </p>
                <p>
                  <strong>Category:</strong> {selectedTransaction.merchant_category}
                </p>
                <p>
                  <strong>Risk score:</strong> {selectedTransaction.risk_score ?? "—"}
                </p>
                <p>
                  <strong>Captured:</strong> {selectedTransaction.timestamp}
                </p>
              </div>
            </div>

            <div className="detail-section">
              <h3>Alerts</h3>
              <ul>
                {selectedTransaction.findings?.length > 0 ? (
                  selectedTransaction.findings.map((finding) => (
                    <li key={finding.title}>
                      <strong>{finding.title}:</strong> {finding.description}
                    </li>
                  ))
                ) : (
                  selectedTransaction.alerts.map((alert) => (
                    <li key={alert}>{formatText(alert)}</li>
                  ))
                )}
              </ul>
            </div>

            <div className="detail-section">
              <h3>Actions</h3>
              <ul>
                {selectedTransaction.actions.length > 0 ? (
                  selectedTransaction.actions.map((action) => (
                    <li key={action}>{formatText(action)}</li>
                  ))
                ) : (
                  <li>No recommended actions</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}
      {selectedCustomer && (
        <CustomerInvestigation
          customer={selectedCustomer}
          transactions={selectedCustomerTxs}
          onClose={() => setSelectedCustomer(null)}
        />
      )}
    </div>
  );
}

function CustomerOverview({ profiles = [], onInspect }) {
  const orderedProfiles = [...profiles].sort((a, b) => {
    const severity = { BLOCKED: 4, REVIEW: 3, MONITOR: 2, APPROVED: 1 };
    return (severity[b.status] || 0) - (severity[a.status] || 0)
      || b.current_day_spend - a.current_day_spend;
  });
  const flagged = orderedProfiles.filter((profile) => profile.status !== "APPROVED");

  return (
    <section className="customer-overview">
      <div className="overview-heading">
        <div>
          <p className="panel-eyebrow">Customer risk monitor</p>
          <h2>{flagged.length} customers need attention</h2>
        </div>
        <p className="overview-note">Select a customer to inspect their behaviour over time.</p>
      </div>
      <div className="customer-grid">
        {orderedProfiles.map((profile) => {
          const utilization = profile.daily_limit
            ? Math.min(profile.current_day_spend / profile.daily_limit, 1.25) * 100
            : 0;
          return (
            <button
              type="button"
              key={profile.customer_id}
              className={`customer-row status-${profile.status.toLowerCase()}`}
              onClick={() => onInspect(profile)}
            >
              <span className="customer-identity">
                <strong>{profile.customer_id}</strong>
                <small>{profile.current_day_transaction_count} today · {profile.transaction_count} total</small>
              </span>
              <span className="customer-spend">
                <strong>€{profile.current_day_spend.toFixed(0)}</strong>
                <small>of €{profile.daily_limit.toFixed(0)}</small>
              </span>
              <span className="customer-meter" aria-label={`${Math.round(utilization)} percent of daily limit`}>
                <span style={{ width: `${Math.min(utilization, 100)}%` }} />
              </span>
              <span className={`customer-status ${profile.status.toLowerCase()}`}>
                {profile.status === "APPROVED" ? "Clear" : profile.latest_alert || profile.status}
              </span>
              <span className="customer-chevron" aria-hidden="true">→</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function CustomerInvestigation({ customer, transactions, onClose }) {
  const profile = customer.profile || customer;
  const dailyTransactions = transactions
    .filter((transaction) => transaction.simulation_day === transactions.at(-1)?.simulation_day)
    .sort((a, b) => (a.timestamp || "").localeCompare(b.timestamp || ""));
  const dailySpend = dailyTransactions.reduce((total, transaction) => total + transaction.amount, 0);
  const dailyLimitFinding = dailyTransactions
    .flatMap((transaction) => transaction.findings || [])
    .find((finding) => finding.title === "High Daily Spend");
  const crossingTransaction = dailyTransactions.find((transaction) =>
    (transaction.findings || []).some((finding) => finding.title === "High Daily Spend")
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="investigation-sheet" onClick={(event) => event.stopPropagation()}>
        <header className="investigation-header">
          <div>
            <p className="panel-eyebrow">Customer investigation</p>
            <h2>{profile.customer_id}</h2>
            <p className="muted-text">Behaviour profile · {profile.transaction_count} transactions observed</p>
          </div>
          <button className="icon-close" type="button" onClick={onClose} aria-label="Close investigation">×</button>
        </header>

        <div className="investigation-summary">
          <div><span>Current state</span><strong className={`summary-state ${String(profile.status).toLowerCase()}`}>{profile.status}</strong></div>
          <div><span>Today</span><strong>€{dailySpend.toFixed(2)}</strong></div>
          <div><span>Daily limit</span><strong>€{profile.daily_limit.toFixed(2)}</strong></div>
          <div><span>Transactions</span><strong>{dailyTransactions.length}</strong></div>
        </div>

        <section className="investigation-section">
          <div className="section-heading">
            <div><p className="panel-eyebrow">Daily behaviour</p><h3>Spend progression</h3></div>
            {crossingTransaction && <span className="crossing-note">Limit crossed at {crossingTransaction.timestamp?.slice(11, 16)}</span>}
          </div>
          <DailySpendViz txs={dailyTransactions} cap={profile.daily_limit} />
          <div className="limit-explanation">
            <span className="limit-key" />
            <p><strong>Customer-specific limit: €{profile.daily_limit.toFixed(0)}</strong><br />
              This limit is set for this customer’s normal activity profile. The chart marks the transaction that pushed today’s cumulative spend beyond it.
            </p>
          </div>
          {dailyLimitFinding?.context && (
            <div className="trigger-callout">
              <strong>Why it was flagged</strong>
              <span>€{dailyLimitFinding.context.spend_before.toFixed(2)} before this payment + €{dailyLimitFinding.context.transaction_amount.toFixed(2)} = €{dailyLimitFinding.context.spend_after.toFixed(2)}</span>
            </div>
          )}
        </section>

        <section className="investigation-section">
          <div className="section-heading"><div><p className="panel-eyebrow">Context</p><h3>What this customer usually does</h3></div></div>
          <div className="profile-facts">
            <div><span>Typical amount</span><strong>€{profile.average_amount.toFixed(2)}</strong></div>
            <div><span>Usual countries</span><strong>{(profile.typical_countries || []).slice(0, 3).map(([country]) => country).join(" · ") || "—"}</strong></div>
            <div><span>Frequent categories</span><strong>{(profile.typical_categories || []).slice(0, 2).map(([category]) => category).join(" · ") || "—"}</strong></div>
          </div>
        </section>

        <section className="investigation-section">
          <div className="section-heading"><div><p className="panel-eyebrow">Activity log</p><h3>Today’s transactions</h3></div><span className="muted-text">{dailyTransactions.length} events</span></div>
          <div className="compact-transaction-list">
            {dailyTransactions.map((transaction) => {
              const flagged = transaction.findings?.length > 0;
              return (
                <div key={transaction.transaction_id} className={`compact-transaction ${flagged ? "flagged" : ""}`}>
                  <span className="compact-time">{transaction.timestamp?.slice(11, 16)}</span>
                  <span className="compact-merchant"><strong>{transaction.merchant}</strong><small>{transaction.merchant_category} · {transaction.country}</small></span>
                  <span className="compact-amount">€{transaction.amount.toFixed(2)}</span>
                  {flagged && <span className="compact-reason">{transaction.findings[0].title}</span>}
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}

function DailySpendViz({ txs = [], cap = 1000 }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    const items = [...txs].sort((a,b) => (a.timestamp||'').localeCompare(b.timestamp||''));
    const labels = items.map(t => (t.timestamp||'').slice(11,16));
    const cumulative = items.reduce((acc, t, i) => { acc.push((acc[i-1]||0) + t.amount); return acc; }, []);
    const crossingIndex = cumulative.findIndex((value) => value > cap);

    if (chartRef.current) chartRef.current.destroy();
    chartRef.current = new window.Chart(ctx, {
      type: 'line',
      data: { labels, datasets: [
        { label: 'Cumulative spend', data: cumulative, borderColor: '#0f766e', backgroundColor: 'rgba(15,118,110,0.08)', pointBackgroundColor: cumulative.map((value, index) => index === crossingIndex ? '#dc2626' : '#0f766e'), pointRadius: cumulative.map((value, index) => index === crossingIndex ? 6 : 3), tension: 0.2, fill: true },
        { label: 'Customer limit', data: labels.map(() => cap), borderColor: '#dc2626', borderDash: [7, 5], pointRadius: 0, tension: 0 }
      ] },
      options: { responsive: true, maintainAspectRatio: false, animation: false, resizeDelay: 0, plugins: { legend: { display: false }, annotation: {} }, scales: { y: { suggestedMin: 0 } }, elements: { line: { fill: false } } }
    });

    return () => { if (chartRef.current) chartRef.current.destroy(); };
  }, [txs, cap]);

  return <div className="daily-spend-chart"><canvas ref={canvasRef} /></div>;
}
