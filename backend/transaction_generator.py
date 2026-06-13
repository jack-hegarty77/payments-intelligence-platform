import random
import uuid
from datetime import datetime
from models import Transaction

# -----------------------------
# Merchant Profiles (realistic spend ranges)
# -----------------------------
MERCHANT_PROFILES = {
    "Tesco": (10, 150),
    "Amazon": (10, 500),
    "Ryanair": (40, 600),
    "Deliveroo": (10, 60),
    "Apple": (1, 2000),
    "Starbucks": (3, 15),
    "Zara": (20, 300),
    "Youngs Pubs": (5, 80),
    "Aldi": (10, 120),
    "NEWRY AND MOURNE COUNCIL": (50, 5000),
}

# Merchant → allowed countries (more realistic modelling)
MERCHANT_COUNTRIES = {
    "Tesco": ["IE", "GB"],
    "Aldi": ["IE", "GB", "DE"],
    "Amazon": ["IE", "GB", "US", "DE", "FR", "ES"],
    "Starbucks": ["IE", "GB", "US"],
    "Deliveroo": ["IE", "GB", "FR"],
    "Zara": ["ES", "FR", "DE", "IE", "GB"],
    "Ryanair": ["IE", "GB", "ES", "FR", "DE"],
    "Apple": ["IE", "US", "GB"],
    "Youngs Pubs": ["GB"],
    "NEWRY AND MOURNE COUNCIL": ["GB"],
}

# High-risk entities
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

# -----------------------------
# Generator
# -----------------------------
def generate_transaction():
    transaction_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    is_high_risk = random.random() < 0.03

    if is_high_risk:
        merchant = random.choice(HIGH_RISK_MERCHANTS)

        return Transaction(
            transaction_id=transaction_id,
            timestamp=timestamp,
            merchant=merchant,
            country=random.choice(SANCTIONED_COUNTRIES),
            amount=round(random.uniform(1000, 5000), 2),
        )

    merchant = random.choice(
        list(MERCHANT_PROFILES.keys())
    )

    min_amount, max_amount = MERCHANT_PROFILES[merchant]

    amount = round(
        random.uniform(min_amount, max_amount),
        2,
    )

    country = random.choice(
        MERCHANT_COUNTRIES[merchant]
    )

    return Transaction(
        transaction_id=transaction_id,
        timestamp=timestamp,
        merchant=merchant,
        country=country,
        amount=amount,
    )