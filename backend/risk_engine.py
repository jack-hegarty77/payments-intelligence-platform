from collections import Counter
from datetime import datetime
import statistics

from models import Transaction, Finding
from simulation_engine import CUSTOMER_PROFILES, MERCHANTS, SANCTIONED_COUNTRIES

# --------------------------------------------------
# Behaviour state
# --------------------------------------------------

customer_daily_totals = {}
customer_profiles = {}
customer_transaction_history = {}


def _parse_timestamp(timestamp: str):
    if not timestamp or timestamp == "manual-check":
        return None

    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def _get_customer_profile(customer_id: str):
    profile = customer_profiles.get(customer_id)

    if profile is None:
        profile = {
            "transaction_count": 0,
            "average_amount": 0.0,
            "median_amount": 0.0,
            "amount_stddev": 0.0,
            "max_amount": 0.0,
            "typical_countries": Counter(),
            "typical_merchants": Counter(),
            "typical_categories": Counter(),
            "last_country": None,
            "last_timestamp": None,
        }
        customer_profiles[customer_id] = profile

    return profile


def _update_customer_profile(transaction: Transaction):
    customer_id = transaction.customer_id
    history = customer_transaction_history.setdefault(customer_id, [])
    history.append(transaction)

    if len(history) > 500:
        history.pop(0)

    profile = _get_customer_profile(customer_id)
    amounts = [tx.amount for tx in history]

    profile["transaction_count"] = len(history)
    profile["average_amount"] = round(statistics.mean(amounts), 2) if amounts else 0.0
    profile["median_amount"] = round(statistics.median(amounts), 2) if amounts else 0.0
    profile["amount_stddev"] = round(statistics.pstdev(amounts), 2) if len(amounts) > 1 else 0.0
    profile["max_amount"] = round(max(amounts), 2) if amounts else 0.0
    profile["typical_countries"] = Counter(
        tx.country for tx in history if tx.country
    )
    profile["typical_merchants"] = Counter(
        tx.merchant for tx in history if tx.merchant
    )
    profile["typical_categories"] = Counter(
        tx.merchant_category for tx in history if tx.merchant_category
    )
    profile["last_country"] = transaction.country
    profile["last_timestamp"] = _parse_timestamp(transaction.timestamp)


def get_customer_profile(customer_id):
    profile = _get_customer_profile(customer_id)
    history = customer_transaction_history.get(customer_id, [])
    current_day = history[-1].simulation_day if history else None
    current_day_history = [
        transaction for transaction in history
        if transaction.simulation_day == current_day
    ]
    daily_total = customer_daily_totals.get(
        (customer_id, current_day),
        0.0,
    ) if current_day is not None else 0.0
    historical_findings = [
        finding
        for transaction in history
        for finding in transaction.findings
    ]
    findings = [
        finding
        for transaction in current_day_history
        for finding in transaction.findings
    ]
    severities = {finding.severity for finding in findings}
    status = (
        "BLOCKED" if "Critical" in severities else
        "REVIEW" if "High" in severities else
        "MONITOR" if "Medium" in severities else
        "APPROVED"
    )

    return {
        "customer_id": customer_id,
        "transaction_count": profile["transaction_count"],
        "average_amount": profile["average_amount"],
        "median_amount": profile["median_amount"],
        "amount_stddev": profile["amount_stddev"],
        "max_amount": profile["max_amount"],
        "typical_countries": profile["typical_countries"].most_common(),
        "typical_merchants": profile["typical_merchants"].most_common(),
        "typical_categories": profile["typical_categories"].most_common(),
        "last_country": profile["last_country"],
        "last_timestamp": (
            profile["last_timestamp"].isoformat()
            if profile["last_timestamp"] else None
        ),
        "current_day_spend": round(daily_total, 2),
        "daily_limit": CUSTOMER_PROFILES.get(customer_id, {}).get("daily_limit", 1000),
        "current_day_transaction_count": len(current_day_history),
        "alert_count": len(findings),
        "latest_alert": findings[-1].title if findings else "",
        "status": status,
        "historical_alert_count": len(historical_findings),
    }


def get_customer_profiles():
    return [
        get_customer_profile(customer_id)
        for customer_id in sorted(CUSTOMER_PROFILES)
    ]


# =====================================================
# DETECTORS
# =====================================================

def geographic_detector(transaction: Transaction):
    findings = []

    if transaction.country in SANCTIONED_COUNTRIES:
        findings.append(
            Finding(
                detector="Geographic",
                severity="Critical",
                title="Sanctioned Country",
                description=f"{transaction.country} is a sanctioned jurisdiction.",
            )
        )

    return findings


def merchant_detector(transaction: Transaction):
    findings = []

    merchant = MERCHANTS.get(transaction.merchant)

    if merchant and merchant["high_risk"]:
        findings.append(
            Finding(
                detector="Merchant",
                severity="High",
                title="High Risk Merchant",
                description="Merchant belongs to a high-risk category.",
            )
        )

    return findings


def amount_detector(transaction: Transaction):
    findings = []

    merchant = MERCHANTS.get(transaction.merchant)

    # Be slightly more tolerant to occasional large catalogue items;
    # require a multiplication factor above the merchant expected maximum.
    if merchant and transaction.amount > merchant["expected_max_amount"] * 1.5:
        findings.append(
            Finding(
                detector="Amount",
                severity="Medium",
                title="Unusual Amount",
                description="Transaction exceeds the expected amount for this merchant.",
            )
        )

    return findings


def behaviour_detector(transaction: Transaction):
    findings = []

    customer = transaction.customer_id
    history = customer_transaction_history.setdefault(customer, [])
    profile = _get_customer_profile(customer)

    # Rapid location change between consecutive transactions
    if history:
        previous_transaction = history[-1]
        previous_timestamp = _parse_timestamp(previous_transaction.timestamp)
        current_timestamp = _parse_timestamp(transaction.timestamp)

        if (
            previous_timestamp
            and current_timestamp
            and previous_transaction.country != transaction.country
            and abs((current_timestamp - previous_timestamp).total_seconds()) <= 15 * 60
        ):
            findings.append(
                Finding(
                    detector="Behaviour",
                    severity="High",
                    title="Impossible Travel",
                    description=(
                        f"Customer moved from {previous_transaction.country} to "
                        f"{transaction.country} within a short time window."
                    ),
                )
            )

    # Spending pattern deviation based on historical customer profile
    # Require a modest amount of history before flagging spending deviations
    if len(history) >= 5 and profile["average_amount"] > 0:
        average_amount = profile["average_amount"]
        standard_deviation = profile["amount_stddev"]
        # Make the deviation detector less sensitive to single outliers
        # while still catching large deviations from a customer's baseline.
        deviation_threshold = max(
            average_amount * 4.0,
            average_amount + max(standard_deviation * 4.0, 100.0),
        )

        if transaction.amount > deviation_threshold:
            severity = "High" if transaction.amount > average_amount * 6 else "Medium"
            findings.append(
                Finding(
                    detector="Behaviour",
                    severity=severity,
                    title="Spending Pattern Deviation",
                    description=(
                        f"Transaction amount {transaction.amount:.2f} is far above the "
                        f"customer's typical spend of {average_amount:.2f}."
                    ),
                )
            )

    # Customer-specific daily spend guardrail
    daily_key = (customer, transaction.simulation_day)
    current_total = customer_daily_totals.get(daily_key, 0)
    new_total = current_total + transaction.amount
    customer_daily_totals[daily_key] = new_total
    daily_limit = CUSTOMER_PROFILES.get(customer, {}).get("daily_limit", 1000)

    if new_total > daily_limit:
        findings.append(
            Finding(
                detector="Behaviour",
                severity="Medium",
                title="High Daily Spend",
                description=(
                    f"Customer has spent {new_total:.2f} today, exceeding their "
                    f"daily limit of {daily_limit:.2f}."
                ),
                context={
                    "period": "day",
                    "limit": daily_limit,
                    "spend_before": round(current_total, 2),
                    "spend_after": round(new_total, 2),
                    "transaction_amount": round(transaction.amount, 2),
                    "transaction_count": len(
                        [tx for tx in history if tx.simulation_day == transaction.simulation_day]
                    ) + 1,
                    "crossed_limit": current_total <= daily_limit,
                },
            )
        )

    _update_customer_profile(transaction)

    return findings


# =====================================================
# DECISION ENGINE
# =====================================================

def make_decision(findings):
    severities = {finding.severity for finding in findings}

    if "Critical" in severities:
        return "BLOCKED"

    if "High" in severities:
        return "REVIEW"

    if "Medium" in severities:
        return "MONITOR"

    return "APPROVED"


# =====================================================
# ACTION ENGINE
# =====================================================

def determine_actions(decision):
    if decision == "BLOCKED":
        return [
            "Payment blocked",
            "Compliance notified",
        ]

    if decision == "REVIEW":
        return [
            "Queued for analyst review",
        ]

    if decision == "MONITOR":
        return [
            "Enhanced monitoring enabled",
        ]

    return []


# =====================================================
# MAIN ENTRY POINT
# =====================================================

def assess_transaction(transaction: Transaction):
    findings = []

    findings.extend(geographic_detector(transaction))
    findings.extend(merchant_detector(transaction))
    findings.extend(amount_detector(transaction))
    findings.extend(behaviour_detector(transaction))

    decision = make_decision(findings)
    actions = determine_actions(decision)

    transaction.decision = decision
    transaction.primary_reason = findings[0].title if findings else ""
    transaction.findings = findings
    transaction.actions = actions

    transaction.status = decision
    transaction.alerts = [
        finding.title.lower().replace(" ", "_")
        for finding in findings
    ]
    transaction.risk_score = len(findings)

    return transaction