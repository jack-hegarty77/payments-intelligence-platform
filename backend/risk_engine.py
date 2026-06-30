from models import Transaction, Finding
from simulation_engine import MERCHANTS, SANCTIONED_COUNTRIES

# --------------------------------------------------
# Behaviour state
# --------------------------------------------------

customer_daily_totals = {}


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

    if merchant:

        if transaction.amount > merchant["expected_max_amount"]:
            findings.append(
                Finding(
                    detector="Amount",
                    severity="Medium",
                    title="Unusual Amount",
                    description="Transaction exceeds the expected amount for this merchant.",
                )
            )

    return findings

def behaviour_detector(transaction):

    findings = []

    customer = transaction.customer_id

    current_total = customer_daily_totals.get(
        customer,
        0,
    )

    new_total = current_total + transaction.amount

    customer_daily_totals[customer] = new_total

    if new_total > 500:

        findings.append(

            Finding(
                detector="Behaviour",
                severity="Medium",
                title="High Daily Spend",
                description=(
                    f"Customer has spent "
                    f"{new_total:.2f} today."
                ),
            )

        )

    return findings


# =====================================================
# DECISION ENGINE
# =====================================================

def make_decision(findings):

    severities = {
        finding.severity
        for finding in findings
    }

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

    findings.extend(
        geographic_detector(transaction)
    )

    findings.extend(
        merchant_detector(transaction)
    )

    findings.extend(
        amount_detector(transaction)
    )

    findings.extend(
    behaviour_detector(transaction)
    )

    decision = make_decision(findings)

    actions = determine_actions(decision)

    # -----------------------------
    # New architecture
    # -----------------------------

    transaction.decision = decision

    transaction.primary_reason = (
        findings[0].title if findings else ""
    )

    transaction.findings = findings

    transaction.actions = actions

    # -----------------------------
    # Temporary frontend compatibility
    # -----------------------------

    transaction.status = decision

    transaction.alerts = [
        finding.title.lower().replace(" ", "_")
        for finding in findings
    ]

    # Temporary placeholder only.
    # This field will disappear once
    # the frontend migrates to decisions.
    transaction.risk_score = len(findings)

    return transaction