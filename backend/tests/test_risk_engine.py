import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import risk_engine
from models import Transaction


def reset_state():
    risk_engine.customer_daily_totals = {}
    risk_engine.customer_profiles = {}
    risk_engine.customer_transaction_history = {}


def make_transaction(customer_id, country, amount, timestamp):
    return Transaction(
        transaction_id=f"{customer_id}-{timestamp}",
        timestamp=timestamp,
        merchant="Tesco",
        country=country,
        amount=amount,
        customer_id=customer_id,
        merchant_category="Groceries",
        simulation_day=0,
        simulation_hour=0,
    )


def test_detects_impossible_travel_between_countries_within_minutes():
    reset_state()

    first = make_transaction("CUST-0001", "GB", 24.5, "2026-01-05T06:00:00")
    second = make_transaction("CUST-0001", "FR", 26.0, "2026-01-05T06:05:00")

    risk_engine.assess_transaction(first)
    result = risk_engine.assess_transaction(second)

    titles = [finding.title for finding in result.findings]
    assert any("Impossible Travel" in title for title in titles)


def test_detects_amount_deviation_from_customer_profile():
    reset_state()

    # Seed multiple baseline transactions so a profile is established
    for i in range(5):
        t = make_transaction("CUST-0002", "GB", 18.0 + (i * 0.5), f"2026-01-05T06:0{i}:00")
        risk_engine.assess_transaction(t)

    suspicious = make_transaction("CUST-0002", "GB", 550.0, "2026-01-05T06:10:00")
    result = risk_engine.assess_transaction(suspicious)

    titles = [finding.title for finding in result.findings]
    assert any("Spending Pattern Deviation" in title for title in titles)
