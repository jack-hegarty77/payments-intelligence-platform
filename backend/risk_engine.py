from models import Transaction


HIGH_RISK_MERCHANTS = [
    "Acme Crypto Exchange",
    "Shadow Trading Ltd",
    "Paypal Transaction",
]

SANCTIONED_COUNTRIES = [
    "IR",
    "KP",
    "SY",
]

MERCHANT_RISK_PROFILES = {
    "Tesco": {
        "large_threshold": 250,
    },
    "Amazon": {
        "large_threshold": 750,
    },
    "Ryanair": {
        "large_threshold": 1000,
    },
    "Deliveroo": {
        "large_threshold": 100,
    },
    "Apple": {
        "large_threshold": 3000,
    },
    "Starbucks": {
        "large_threshold": 30,
    },
    "Zara": {
        "large_threshold": 500,
    },
    "Youngs Pubs": {
        "large_threshold": 120,
    },
    "Aldi": {
        "large_threshold": 250,
    },
    "NEWRY AND MOURNE COUNCIL": {
        "large_threshold": 10000,
    },
}


def determine_status_and_actions(risk_score):
    if risk_score >= 100:
        return (
            "BLOCKED",
            [
                "payment_blocked",
                "compliance_alert_generated",
            ],
        )

    if risk_score >= 75:
        return (
            "REVIEW",
            [
                "manual_review_required",
            ],
        )

    if risk_score >= 50:
        return (
            "NOTIFY",
            [
                "customer_notified",
            ],
        )

    if risk_score >= 25:
        return (
            "MONITOR",
            [
                "transaction_logged",
            ],
        )

    return (
        "APPROVED",
        [],
    )


def assess_transaction(transaction: Transaction):
    risk_score = 0
    alerts = []

    merchant = transaction.merchant
    country = transaction.country
    amount = transaction.amount

    # -------------------------
    # High Risk Merchant
    # -------------------------
    if merchant in HIGH_RISK_MERCHANTS:
        risk_score += 40
        alerts.append("high_risk_merchant")

    # -------------------------
    # Sanctioned Country
    # -------------------------
    if country in SANCTIONED_COUNTRIES:
        risk_score += 100
        alerts.append("sanctioned_country")

    # -------------------------
    # Merchant Amount Anomaly
    # -------------------------
    if merchant in MERCHANT_RISK_PROFILES:
        threshold = MERCHANT_RISK_PROFILES[merchant][
            "large_threshold"
        ]

        if amount > threshold:
            risk_score += 25
            alerts.append(
                "unusual_transaction_amount"
            )

    # -------------------------
    # Decision
    # -------------------------
    status, actions = (
        determine_status_and_actions(
            risk_score
        )
    )

    # Populate model
    transaction.risk_score = risk_score
    transaction.status = status
    transaction.alerts = alerts
    transaction.actions = actions

    return transaction