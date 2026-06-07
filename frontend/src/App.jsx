import { useEffect, useState } from "react";
import "./App.css";

function formatText(text) {
  return text
    .split("_")
    .map(
      (word) =>
        word.charAt(0).toUpperCase() +
        word.slice(1)
    )
    .join(" ");
}

function getPrimaryReason(tx) {
  if (tx.alerts.includes("sanctioned_country")) {
    return "Sanctioned Country";
  }

  if (tx.alerts.includes("high_risk_merchant")) {
    return "High Risk Merchant";
  }

  if (
    tx.alerts.includes(
      "unusual_transaction_amount"
    )
  ) {
    return "Unusual Transaction Amount";
  }

  return "Under Investigation";
}

export default function App() {
  const [transactions, setTransactions] =
    useState([]);

  const [
    selectedTransaction,
    setSelectedTransaction,
  ] = useState(null);

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/transactions/live"
        );

        const data = await response.json();
        setTransactions(data);
      } catch (error) {
        console.error("Fetch error:", error);
      }
    };

    fetchTransactions();

    const interval = setInterval(
      fetchTransactions,
      2000
    );

    return () => clearInterval(interval);
  }, []);

  const approvedTransactions = transactions
    .filter((tx) => tx.status === "APPROVED")
    .slice(-10)
    .reverse();

  const riskyTransactions = transactions
    .filter(
      (tx) =>
        tx.status === "REVIEW" ||
        tx.status === "BLOCKED"
    )
    .reverse();

  const counts = {
    APPROVED: transactions.filter(
      (t) => t.status === "APPROVED"
    ).length,
    MONITOR: transactions.filter(
      (t) => t.status === "MONITOR"
    ).length,
    NOTIFY: transactions.filter(
      (t) => t.status === "NOTIFY"
    ).length,
    REVIEW: transactions.filter(
      (t) => t.status === "REVIEW"
    ).length,
    BLOCKED: transactions.filter(
      (t) => t.status === "BLOCKED"
    ).length,
  };

  return (
    <div className="dashboard">
      <header className="header">
        <h1>
          Payments Intelligence Platform
        </h1>
      </header>

      {/* SUMMARY */}
      <div className="summary-grid">
        <div className="summary-card">
          <h2>{counts.APPROVED}</h2>
          <p>Approved</p>
        </div>

        <div className="summary-card">
          <h2>{counts.MONITOR}</h2>
          <p>Monitor</p>
        </div>

        <div className="summary-card">
          <h2>{counts.NOTIFY}</h2>
          <p>Notify</p>
        </div>

        <div className="summary-card">
          <h2>{counts.REVIEW}</h2>
          <p>Review</p>
        </div>

        <div className="summary-card blocked-tile">
          <h2>{counts.BLOCKED}</h2>
          <p>Blocked</p>
        </div>
      </div>

      {/* MAIN GRID */}
      <div className="content-grid">

        {/* APPROVED */}
        <section className="panel">
          <h2>✅ Approved Feed</h2>

          {approvedTransactions.map((tx) => (
            <div
              key={tx.transaction_id}
              className="approved-card"
            >
              <strong>{tx.merchant}</strong>
              <p>
                €{tx.amount} · {tx.country}
              </p>
            </div>
          ))}
        </section>

        {/* RISK QUEUE */}
        <section className="panel risk-panel">
          <h2>🚨 Risk Queue</h2>

          {riskyTransactions.map((tx) => (
            <div
              key={tx.transaction_id}
              className="risk-card"
              onClick={() =>
                setSelectedTransaction(tx)
              }
            >
              <div className="risk-card-header">
                <h3>{tx.merchant}</h3>

                <span
                  className={`status-badge ${tx.status.toLowerCase()}`}
                >
                  {tx.status}
                </span>
              </div>

              <p>
                €{tx.amount} · {tx.country}
              </p>

              <p className="primary-reason">
                {getPrimaryReason(tx)}
              </p>
            </div>
          ))}
        </section>

        {/* SUMMARY PANEL */}
        <section className="panel">
          <h2>📊 Alert Summary</h2>

          <p>
            Monitoring active across all
            incoming payments.
          </p>

          <p>
            Click a risk alert to investigate.
          </p>
        </section>
      </div>

      {/* MODAL */}
      {selectedTransaction && (
        <div
          className="modal-overlay"
          onClick={() =>
            setSelectedTransaction(null)
          }
        >
          <div
            className="modal"
            onClick={(e) =>
              e.stopPropagation()
            }
          >
            <h2>
              Transaction Investigation
            </h2>

            <p>
              <strong>Merchant:</strong>{" "}
              {
                selectedTransaction.merchant
              }
            </p>

            <p>
              <strong>Amount:</strong> €
              {selectedTransaction.amount}
            </p>

            <p>
              <strong>Country:</strong>{" "}
              {
                selectedTransaction.country
              }
            </p>

            <p>
              <strong>Status:</strong>{" "}
              {
                selectedTransaction.status
              }
            </p>

            <h3>Alerts</h3>
            <ul>
              {selectedTransaction.alerts.map(
                (a) => (
                  <li key={a}>
                    {formatText(a)}
                  </li>
                )
              )}
            </ul>

            <h3>Actions</h3>
            <ul>
              {selectedTransaction.actions.map(
                (a) => (
                  <li key={a}>
                    {formatText(a)}
                  </li>
                )
              )}
            </ul>

            <button
              onClick={() =>
                setSelectedTransaction(null)
              }
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}