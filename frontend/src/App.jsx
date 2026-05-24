import { useState } from "react";

function App() {
  const [merchant, setMerchant] = useState("");
  const [amount, setAmount] = useState("");
  const [country, setCountry] = useState("IE");

  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const submitPayment = async () => {
    const payment = {
      merchant,
      amount: Number(amount),
      country,
    };

    const response = await fetch(
      "http://127.0.0.1:8000/payments/check",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payment),
      }
    );

    const data = await response.json();

    setResult(data);

    setHistory([
      {
        ...payment,
        ...data,
      },
      ...history,
    ]);

    setMerchant("");
    setAmount("");
    setCountry("IE");
  };

  return (
    <div
      style={{
        maxWidth: "700px",
        margin: "40px auto",
        fontFamily: "Arial",
      }}
    >
      <h1>Payments Risk Dashboard</h1>

      <div
        style={{
          padding: "20px",
          border: "1px solid #ddd",
          borderRadius: "10px",
        }}
      >
        <input
          placeholder="Merchant"
          value={merchant}
          onChange={(e) => setMerchant(e.target.value)}
        />

        <br /><br />

        <input
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />

        <br /><br />

        <input
          placeholder="Country"
          value={country}
          onChange={(e) => setCountry(e.target.value)}
        />

        <br /><br />

        <button onClick={submitPayment}>
          Check Risk
        </button>
      </div>

      {result && (
        <div style={{ marginTop: "30px" }}>
          <h2>Latest Result</h2>
          <p>Risk Score: {result.risk_score}</p>

          <ul>
            {result.alerts.map((alert) => (
              <li key={alert}>{alert}</li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ marginTop: "40px" }}>
        <h2>Payment History</h2>

        {history.map((payment, index) => (
          <div
            key={index}
            style={{
              border: "1px solid #ddd",
              padding: "15px",
              borderRadius: "10px",
              marginBottom: "10px",
            }}
          >
            <strong>{payment.merchant}</strong>

            <p>
              €{payment.amount} — {payment.country}
            </p>

            <p>
              Risk Score: {payment.risk_score}
            </p>

            <p>
              Alerts: {payment.alerts.join(", ") || "None"}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;