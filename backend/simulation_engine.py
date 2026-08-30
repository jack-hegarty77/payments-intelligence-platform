import random
import uuid
from datetime import datetime
from datetime import datetime, timedelta

from models import Transaction

# --------------------------------------------------
# Simulation Clock
# --------------------------------------------------

SIMULATION_START = datetime(2026, 1, 5, 6, 0, 0)

simulation_time = SIMULATION_START

# speed: 1 loop = 1 simulated minute
TIME_STEP_MINUTES = 1

# --------------------------------------------------
# Simulation Clock
# --------------------------------------------------

CUSTOMER_COUNT = 100

# Fewer customers but higher activity per customer improves signal
CUSTOMERS = [f"CUST-{i:04d}" for i in range(1, CUSTOMER_COUNT + 1)]

# Per-customer activity/profile metadata: baseline multiplier and weight
CUSTOMER_PROFILES = {}
for i, cid in enumerate(CUSTOMERS, start=1):
    # heavier tail: few highly active customers, many less active
    weight = max(1, int((CUSTOMER_COUNT - i) / 6) + 1)
    # baseline multiplier varies to create distinct spend patterns
    baseline = 0.6 + (i % 10) * 0.16
    CUSTOMER_PROFILES[cid] = {"weight": weight, "baseline": baseline}

# -----------------------------
# Merchant Profiles
# -----------------------------
# --------------------------------------------------
# Merchant Catalogue
# --------------------------------------------------

MERCHANTS = {

    "Tesco": {
        "category": "Groceries",
        "countries": ["GB", "IE"],
        "amount_range": (5, 180),
        "expected_max_amount": 250,
        "weight": 20,
        "busy_hours": range(16, 21),
        "high_risk": False,
    },

    "Amazon": {
        "category": "Retail",
        "countries": ["GB", "IE", "US", "DE", "FR", "ES"],
        "amount_range": (10, 600),
        "expected_max_amount": 750,
        "weight": 18,
        "busy_hours": range(10, 22),
        "high_risk": False,
    },

    "Ryanair": {
        "category": "Travel",
        "countries": ["IE", "GB", "ES", "FR", "DE"],
        "amount_range": (40, 350),
        "expected_max_amount": 1000,
        "weight": 5,
        "busy_hours": range(0, 24),
        "high_risk": False,
    },

    "Deliveroo": {
        "category": "Food Delivery",
        "countries": ["GB", "IE", "FR"],
        "amount_range": (12, 60),
        "expected_max_amount": 100,
        "weight": 14,
        "busy_hours": range(18, 22),
        "high_risk": False,
    },

    "Apple": {
        "category": "Technology",
        "countries": ["GB", "IE", "US"],
        "amount_range": (500, 2500),
        "expected_max_amount": 3000,
        "weight": 3,
        "busy_hours": range(9, 21),
        "high_risk": False,
    },

    "Starbucks": {
        "category": "Coffee",
        "countries": ["GB", "IE", "US"],
        "amount_range": (2, 15),
        "expected_max_amount": 30,
        "weight": 15,
        "busy_hours": range(7, 11),
        "high_risk": False,
    },

    "Youngs Pubs": {
        "category": "Hospitality",
        "countries": ["GB"],
        "amount_range": (10, 80),
        "expected_max_amount": 120,
        "weight": 6,
        "busy_hours": range(18, 24),
        "high_risk": False,
    },

    "Aldi": {
        "category": "Groceries",
        "countries": ["GB", "IE", "DE"],
        "amount_range": (10, 140),
        "expected_max_amount": 250,
        "weight": 12,
        "busy_hours": range(16, 20),
        "high_risk": False,
    },

    "NEWRY AND MOURNE COUNCIL": {
        "category": "Government",
        "countries": ["GB"],
        "amount_range": (500, 8000),
        "expected_max_amount": 10000,
        "weight": 1,
        "busy_hours": range(8, 17),
        "high_risk": False,
    },

    "Sainsbury's": {
        "category": "Groceries",
        "countries": ["GB"],
        "amount_range": (8, 170),
        "expected_max_amount": 250,
        "weight": 15,
        "busy_hours": range(16, 21),
        "high_risk": False,
    },

    "Marks & Spencer": {
        "category": "Retail",
        "countries": ["GB", "IE"],
        "amount_range": (20, 300),
        "expected_max_amount": 500,
        "weight": 8,
        "busy_hours": range(11, 19),
        "high_risk": False,
    },

    "Uber": {
        "category": "Transport",
        "countries": ["GB", "IE", "US", "FR"],
        "amount_range": (6, 80),
        "expected_max_amount": 120,
        "weight": 12,
        "busy_hours": range(6, 24),
        "high_risk": False,
    },

    "Uber Eats": {
        "category": "Food Delivery",
        "countries": ["GB", "IE"],
        "amount_range": (10, 65),
        "expected_max_amount": 100,
        "weight": 10,
        "busy_hours": range(18, 23),
        "high_risk": False,
    },

    "Boots": {
        "category": "Pharmacy",
        "countries": ["GB", "IE"],
        "amount_range": (5, 120),
        "expected_max_amount": 200,
        "weight": 8,
        "busy_hours": range(9, 18),
        "high_risk": False,
    },

    "Shell": {
        "category": "Fuel",
        "countries": ["GB", "IE"],
        "amount_range": (20, 120),
        "expected_max_amount": 180,
        "weight": 10,
        "busy_hours": range(6, 22),
        "high_risk": False,
    },

    "Netflix": {
        "category": "Entertainment",
        "countries": ["GB", "IE", "US"],
        "amount_range": (8, 20),
        "expected_max_amount": 25,
        "weight": 4,
        "busy_hours": range(0, 24),
        "high_risk": False,
    },

    "Spotify": {
        "category": "Entertainment",
        "countries": ["GB", "IE", "US"],
        "amount_range": (8, 20),
        "expected_max_amount": 25,
        "weight": 4,
        "busy_hours": range(0, 24),
        "high_risk": False,
    },

    "B&Q": {
        "category": "Home Improvement",
        "countries": ["GB", "IE"],
        "amount_range": (15, 600),
        "expected_max_amount": 900,
        "weight": 5,
        "busy_hours": range(9, 18),
        "high_risk": False,
    },

    "Currys": {
        "category": "Electronics",
        "countries": ["GB", "IE"],
        "amount_range": (40, 1800),
        "expected_max_amount": 2500,
        "weight": 4,
        "busy_hours": range(10, 20),
        "high_risk": False,
    },

    # -------------------------
    # High-risk entities
    # -------------------------

    "Acme Crypto Exchange": {
        "category": "Cryptocurrency",
        "countries": ["KP"],
        "amount_range": (1000, 5000),
        "expected_max_amount": 1000,
        "weight": 0,
        "busy_hours": range(0, 24),
        "high_risk": True,
    },

    "Shadow Trading Ltd": {
        "category": "Financial Services",
        "countries": ["SY"],
        "amount_range": (1500, 7000),
        "expected_max_amount": 1000,
        "weight": 0,
        "busy_hours": range(0, 24),
        "high_risk": True,
    },

    "Paypal Transaction": {
        "category": "Money Transfer",
        "countries": ["GB", "IE", "US"],
        "amount_range": (500, 4000),
        "expected_max_amount": 750,
        "weight": 0,
        "busy_hours": range(0, 24),
        "high_risk": True,
    },
}

# --------------------------------------------------
# Sanctioned Countries
# --------------------------------------------------

SANCTIONED_COUNTRIES = {
    "IR",
    "KP",
    "SY",
}

# --------------------------------------------------
# Weighted Merchant Selection
# --------------------------------------------------

def pick_merchant():
    merchants = list(MERCHANTS.keys())
    weights = [MERCHANTS[m]["weight"] for m in merchants]
    return random.choices(merchants, weights=weights, k=1)[0]


def pick_customer():
    customers = CUSTOMER_PROFILES.keys()
    weights = [CUSTOMER_PROFILES[c]["weight"] for c in customers]
    return random.choices(list(customers), weights=weights, k=1)[0]

# --------------------------------------------------
# Transaction Generation
# --------------------------------------------------

ANOMALY_RATE = 0.02

# assign home country and chance to transact abroad
COMMON_COUNTRIES = ['GB', 'IE', 'US', 'DE', 'FR', 'ES']
for cid, profile in CUSTOMER_PROFILES.items():
    # bias home country to GB/IE for most customers
    home = random.choice(['GB'] * 6 + ['IE'] * 3 + ['US', 'DE', 'FR', 'ES'])
    profile['home_country'] = home
    # small probability of choosing a country outside home during normal transactions
    profile['country_switch_prob'] = 0.03

def advance_clock():
    global simulation_time
    simulation_time += timedelta(minutes=TIME_STEP_MINUTES)
    return simulation_time


def build_transaction(merchant_name, customer_id, country, amount):
    merchant=MERCHANTS[merchant_name]
    current_time=advance_clock()
    return Transaction(transaction_id=str(uuid.uuid4()),timestamp=current_time.isoformat(),merchant=merchant_name,country=country,amount=round(amount,2),customer_id=customer_id,merchant_category=merchant['category'],simulation_day=(current_time-SIMULATION_START).days,simulation_hour=current_time.hour)


def generate_normal_transaction():
    merchant_name = pick_merchant()
    merchant = MERCHANTS[merchant_name]
    customer_id = pick_customer()
    profile = CUSTOMER_PROFILES.get(customer_id, {})

    # choose country: prefer customer's home country where possible
    if random.random() < (1 - profile.get('country_switch_prob', 0.03)) and profile.get('home_country') in merchant['countries']:
        country = profile.get('home_country')
    else:
        country = random.choice(merchant['countries'])

    min_amt, max_amt = merchant['amount_range']
    # pick a base amount within the merchant range
    base = random.uniform(min_amt, max_amt)

    # apply customer's baseline and small gaussian noise for smoother series
    profile = CUSTOMER_PROFILES.get(customer_id, {"baseline": 1.0})
    baseline = profile.get("baseline", 1.0)
    noise = random.gauss(1.0, 0.08)
    amount = base * baseline * noise

    # busy hours increase slightly but deterministically
    if simulation_time.hour in merchant['busy_hours']:
        amount *= 1.08

    # clamp amount to reasonable merchant bounds
    amount = max(min_amt * 0.8, min(amount, max_amt * 1.2))
    return build_transaction(merchant_name, customer_id, country, amount)


def generate_anomalous_transaction():
    anomaly=random.choice(['high_risk_merchant','sanctioned_country','large_amount'])
    tx=generate_normal_transaction()
    if anomaly=='high_risk_merchant':
        candidates=[m for m,v in MERCHANTS.items() if v['high_risk']]
        merchant_name=random.choice(candidates); merchant=MERCHANTS[merchant_name]
        return build_transaction(merchant_name,tx.customer_id,random.choice(merchant['countries']),random.uniform(*merchant['amount_range']))
    if anomaly=='sanctioned_country':
        tx.country=random.choice(list(SANCTIONED_COUNTRIES)); return tx
    merchant=MERCHANTS[tx.merchant]
    tx.amount=round(merchant['expected_max_amount']*random.uniform(1.4,2.2),2)
    return tx


def generate_transaction():
    if random.random()<ANOMALY_RATE:
        return generate_anomalous_transaction()
    return generate_normal_transaction()
