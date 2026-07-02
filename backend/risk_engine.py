from collections import Counter
from datetime import datetime
import statistics

from models import Transaction, Finding
from simulation_engine import MERCHANTS, SANCTIONED_COUNTRIES

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

    if len(history) > 50:
        history.pop(0)

    profile = _get_customer_profile(customer_id)
    amounts = [tx.amount for tx in history]

    profile["transaction_count"] = len(history)
    profile["average_amount"] = round(statistics.mean(amounts), 2) if amounts else 0.0
    profile["median_amount"] = round(statistics.median(amounts), 2) if amounts else 0.0
    profile["amount_stddev"] = round(statistics.pstdev(amounts), 2) if len(amounts) > 1 else 0.0
    profile["max_amount"] = round(max(amounts), 2) if amounts else 0.0
    profile["typical_countries"].update(
        tx.country for tx in history if tx.country
    )
    profile["typical_merchants"].update(
        tx.merchant for tx in history if tx.merchant
    )
    profile["typical_categories"].update(
        tx.merchant_category for tx in history if tx.merchant_category
    )
    profile["last_country"] = transaction.country
    profile["last_timestamp"] = _parse_timestamp(transaction.timestamp)


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

    if merchant and transaction.amount > merchant["expected_max_amount"]:
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
    if len(history) >= 1 and profile["average_amount"] > 0:
        average_amount = profile["average_amount"]
        standard_deviation = profile["amount_stddev"]
        deviation_threshold = max(
            average_amount * 2.5,
            average_amount + max(standard_deviation * 3, 50.0),
        )

        if transaction.amount > deviation_threshold:
            severity = "High" if transaction.amount > average_amount * 5 else "Medium"
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

    # Daily spend guardrail
    current_total = customer_daily_totals.get(customer, 0)
    new_total = current_total + transaction.amount
    customer_daily_totals[customer] = new_total

    if new_total > 500:
        findings.append(
            Finding(
                detector="Behaviour",
                severity="Medium",
                title="High Daily Spend",
                description=f"Customer has spent {new_total:.2f} today.",
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