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

function getPrimaryReason(tx) {
  if (tx.primary_reason) {
    return tx.primary_reason;
  }

  if (tx.alerts?.includes("sanctioned_country")) {
    return "Sanctioned Country";
  }

  if (tx.alerts?.includes("high_risk_merchant")) {
    return "High Risk Merchant";
  }

  if (tx.alerts?.includes("unusual_transaction_amount")) {
    return "Unusual Transaction Amount";
  }

  if (tx.alerts?.length) {
    return formatText(tx.alerts[0]);
  }

  return "Under Investigation";
}

function getTickerClass(tx) {
  const status = getDisplayStatus(tx);

  switch (status) {
    case "BLOCKED":
      return "ticker-card blocked";
    case "REVIEW":
      return "ticker-card review";
    case "MONITOR":
      return "ticker-card monitor";
    case "NOTIFY":
      return "ticker-card notify";
    default:
      return "ticker-card approved";
  }
}

export default function App() {
  const [transactions, setTransactions] = useState([]);
  const [selectedTransaction, setSelectedTransaction] =
    useState(null);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [selectedCustomerTxs, setSelectedCustomerTxs] = useState([]);
  const [connected, setConnected] = useState(false);
  const [statusMessage, setStatusMessage] =
    useState("Connecting to live feed...");
  const [errorMessage, setErrorMessage] = useState("");

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
      } catch (error) {
        setErrorMessage(
          "Unable to load recent transactions."
        );
      }
    }

    loadInitial();

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

    return () => socket.close();
  }, []);

  const recentTransactions = [...transactions].reverse();
  const tickerTransactions = recentTransactions.slice(0, 30);
  const monitorTransactions = recentTransactions.filter(
    (tx) => getDisplayStatus(tx) === "MONITOR"
  );
  const escalationTransactions = recentTransactions.filter((tx) =>
    ["REVIEW", "BLOCKED", "NOTIFY"].includes(
      getDisplayStatus(tx)
    )
  );

  const counts = transactions.reduce(
    (acc, tx) => {
      const status = getDisplayStatus(tx);
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    },
    {
      APPROVED: 0,
      MONITOR: 0,
      NOTIFY: 0,
      REVIEW: 0,
      BLOCKED: 0,
    }
  );

  // latest transaction for simulated time
  const latestTx = recentTransactions[0] || null;

  function groupByCustomer(list) {
    const map = {};
    (list || []).forEach((tx) => {
      const cid = tx.customer_id || "unknown";
      if (!map[cid]) map[cid] = [];
      map[cid].push(tx);
    });

    const groups = Object.keys(map).map((cid) => {
      const txs = map[cid].sort((a, b) => (b.timestamp || "").localeCompare(a.timestamp || ""));
      const count = txs.length;
      const total = txs.reduce((s, t) => s + (t.amount || 0), 0);
      const lastSeen = txs[0]?.timestamp || "";
      const riskCount = txs.filter((t) => (t.findings?.length || t.alerts?.length)).length;
      return { customer_id: cid, txs, count, total, lastSeen, riskCount };
    });

    groups.sort((a, b) => b.riskCount - a.riskCount || (b.lastSeen || "").localeCompare(a.lastSeen || ""));
    return groups;
  }

  const monitorCustomers = groupByCustomer(monitorTransactions);
  const escalationCustomers = groupByCustomer(escalationTransactions);

  return (
    <div className="dashboard">
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

      <section className="ticker-container">
        {tickerTransactions.length > 0 ? (
          <Marquee items={tickerTransactions} getClass={getTickerClass} />
        ) : (
          <div className="ticker-empty">Waiting for live transactions...</div>
        )}
      </section>

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

      <div className="investigation-grid">
        <section className="panel panel-monitor">
          <div className="panel-heading">
            <div>
              <p className="panel-eyebrow">Monitoring queue</p>
              <h2>Monitor alerts</h2>
            </div>
            <span className="panel-pill monitor-pill">
              {monitorTransactions.length} active
            </span>
          </div>
          <p className="panel-copy">
            Transactions requiring additional observation before a final disposition.
          </p>
          {monitorCustomers.length > 0 ? (
            monitorCustomers.slice(0, 10).map((c) => (
              <div
                key={c.customer_id}
                className="investigation-card monitor-card"
                onClick={() => {
                  setSelectedCustomer(c);
                  setSelectedCustomerTxs(c.txs);
                }}
              >
                <div className="investigation-card-top">
                  <div>
                    <h3>{c.customer_id}</h3>
                    <p className="muted-text">{c.count} transactions · €{c.total.toFixed(2)}</p>
                  </div>
                  <span className="panel-pill monitor-pill">{c.riskCount} alerts</span>
                </div>
                <div className="investigation-card-body">
                  <p className="primary-reason">{c.txs[0] ? getPrimaryReason(c.txs[0]) : ''}</p>
                  <p className="muted-text">Last: {c.lastSeen?.slice(11,16) || '—'}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">
              No monitor alerts pending.
            </div>
          )}
        </section>

        <section className="panel panel-escalation">
          <div className="panel-heading">
            <div>
              <p className="panel-eyebrow">Escalation lane</p>
              <h2>Review and blocked</h2>
            </div>
            <span className="panel-pill escalation-pill">
              {escalationTransactions.length} needs attention
            </span>
          </div>
          <p className="panel-copy">
            High-priority cases that require analyst review or immediate blocking.
          </p>
          {escalationCustomers.length > 0 ? (
            escalationCustomers.slice(0, 10).map((c) => (
              <div
                key={c.customer_id}
                className="investigation-card escalation-card"
                onClick={() => {
                  setSelectedCustomer(c);
                  setSelectedCustomerTxs(c.txs);
                }}
              >
                <div className="investigation-card-top">
                  <div>
                    <h3>{c.customer_id}</h3>
                    <p className="muted-text">{c.count} transactions · €{c.total.toFixed(2)}</p>
                  </div>
                  <span className={`panel-pill escalation-pill`}>{c.riskCount} alerts</span>
                </div>
                <div className="investigation-card-body">
                  <p className="primary-reason">{c.txs[0] ? getPrimaryReason(c.txs[0]) : ''}</p>
                  <p className="muted-text">Last: {c.lastSeen?.slice(11,16) || '—'}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">
              No escalations in the queue.
            </div>
          )}
        </section>
      </div>

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
        <div
          className="modal-overlay"
          onClick={() => setSelectedCustomer(null)}
        >
          <div
            className="modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="modal-header">
              <div>
                <h2>Customer Investigation</h2>
                <p className="muted-text">{selectedCustomer.customer_id}</p>
              </div>
              <button
                className="close-button"
                onClick={() => setSelectedCustomer(null)}
              >
                Close
              </button>
            </div>

            <div className="detail-section">
              <h3>Transactions (latest)</h3>
              <ul className="tx-history-list">
                {selectedCustomerTxs.map((tx) => (
                  <li key={tx.transaction_id} className={(tx.findings?.length || tx.alerts?.length) ? 'suspicious' : 'normal'}>
                    <div className="tx-row">
                      <div>
                        <strong>{tx.merchant}</strong>
                        <div className="muted-text">{tx.timestamp?.slice(11,16)} · {tx.country}</div>
                      </div>
                      <div>
                        <div>€{tx.amount.toFixed(2)}</div>
                        <div className="status-badge">{getDisplayStatus(tx)}</div>
                      </div>
                    </div>
                    {(tx.findings?.length > 0)
                      ? tx.findings.map((f) => (
                          <div key={f.title} className="finding"><strong>{f.title}:</strong> {f.description}</div>
                        ))
                      : tx.alerts?.map((a) => <div key={a} className="finding">{formatText(a)}</div>)}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Marquee({ items, getClass }) {
  const trackRef = useRef(null);
  const offsetRef = useRef(0);
  const frameRef = useRef(null);
  const singleWidthRef = useRef(0);

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;

    // measure single content width (we duplicate items)
    singleWidthRef.current = track.scrollWidth / 2 || 0;

    // if the content is shorter than the viewport, don't animate — keep static
    const viewportWidth = track.parentElement?.clientWidth || 0;
    if (singleWidthRef.current <= viewportWidth) {
      offsetRef.current = 0;
      track.style.transform = `translateX(0)`;
      return;
    }

    // ensure offset is within the new width to avoid visible jumps on items change
    if (singleWidthRef.current > 0) {
      offsetRef.current = offsetRef.current % singleWidthRef.current;
    } else {
      offsetRef.current = 0;
    }

    let lastTime = performance.now();
    const speed = 60; // pixels per second

    function step(now) {
      const dt = (now - lastTime) / 1000;
      lastTime = now;
      offsetRef.current += speed * dt;
      if (singleWidthRef.current > 0 && offsetRef.current >= singleWidthRef.current) {
        offsetRef.current -= singleWidthRef.current;
      }
      track.style.transform = `translateX(${-offsetRef.current}px)`;
      frameRef.current = requestAnimationFrame(step);
    }

    frameRef.current = requestAnimationFrame(step);

    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [items]);

  // render two copies for seamless loop
  return (
    <div className="ticker-viewport">
      <div className="ticker-track" ref={trackRef} style={{transform: 'translateX(0)'}}>
        {items.map((tx, i) => (
          <div key={`A-${tx.transaction_id}-${i}`} className={getClass(tx)}>
            <span className="ticker-time">{tx.timestamp?.slice(11,16) || '--:--'}</span>
            <span>{tx.customer_id}</span>
            <span>{tx.merchant}</span>
            <span>€{tx.amount.toFixed(2)}</span>
          </div>
        ))}
        {items.map((tx, i) => (
          <div key={`B-${tx.transaction_id}-${i}`} className={getClass(tx)}>
            <span className="ticker-time">{tx.timestamp?.slice(11,16) || '--:--'}</span>
            <span>{tx.customer_id}</span>
            <span>{tx.merchant}</span>
            <span>€{tx.amount.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
