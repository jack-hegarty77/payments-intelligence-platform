import { useEffect, useState } from "react";
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

  const summaryCards = [
    { label: "Approved", value: counts.APPROVED, tone: "approved" },
    { label: "Monitor", value: counts.MONITOR, tone: "monitor" },
    { label: "Notify", value: counts.NOTIFY, tone: "notify" },
    { label: "Review", value: counts.REVIEW, tone: "review" },
    { label: "Blocked", value: counts.BLOCKED, tone: "blocked" },
  ];

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
          <div className="ticker-track">
            {[...tickerTransactions, ...tickerTransactions].map(
              (tx, index) => (
                <div
                  key={`${tx.transaction_id}-${index}`}
                  className={getTickerClass(tx)}
                >
                  <span className="ticker-time">
                    {tx.timestamp?.slice(11, 16) || "--:--"}
                  </span>
                  <span>{tx.customer_id}</span>
                  <span>{tx.merchant}</span>
                  <span>€{tx.amount.toFixed(2)}</span>
                </div>
              )
            )}
          </div>
        ) : (
          <div className="ticker-empty">
            Waiting for live transactions...
          </div>
        )}
      </section>

      <div className="summary-grid">
        {summaryCards.map((card) => (
          <div
            key={card.label}
            className={`summary-card ${card.tone}`}
          >
            <p className="summary-label">{card.label}</p>
            <h2>{card.value}</h2>
          </div>
        ))}
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
          {monitorTransactions.length > 0 ? (
            monitorTransactions.slice(0, 8).map((tx) => (
              <div
                key={tx.transaction_id}
                className="investigation-card monitor-card"
                onClick={() => setSelectedTransaction(tx)}
              >
                <div className="investigation-card-top">
                  <div>
                    <h3>{tx.merchant}</h3>
                    <p className="muted-text">
                      {tx.country} · {tx.customer_id}
                    </p>
                  </div>
                  <span className="status-badge monitor">Monitor</span>
                </div>
                <div className="investigation-card-body">
                  <p className="risk-amount">€{tx.amount.toFixed(2)}</p>
                  <p className="primary-reason">{getPrimaryReason(tx)}</p>
                </div>
                <div className="risk-meta">
                  <span>Risk score {tx.risk_score ?? "—"}</span>
                  <span>{tx.timestamp?.slice(11, 16) || "—"}</span>
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
          {escalationTransactions.length > 0 ? (
            escalationTransactions.slice(0, 8).map((tx) => (
              <div
                key={tx.transaction_id}
                className="investigation-card escalation-card"
                onClick={() => setSelectedTransaction(tx)}
              >
                <div className="investigation-card-top">
                  <div>
                    <h3>{tx.merchant}</h3>
                    <p className="muted-text">
                      {tx.country} · {tx.customer_id}
                    </p>
                  </div>
                  <span
                    className={`status-badge ${
                      getDisplayStatus(tx).toLowerCase()
                    }`}
                  >
                    {getDisplayStatus(tx)}
                  </span>
                </div>
                <div className="investigation-card-body">
                  <p className="risk-amount">€{tx.amount.toFixed(2)}</p>
                  <p className="primary-reason">{getPrimaryReason(tx)}</p>
                </div>
                <div className="risk-meta">
                  <span>Risk score {tx.risk_score ?? "—"}</span>
                  <span>{tx.timestamp?.slice(11, 16) || "—"}</span>
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
    </div>
  );
}
