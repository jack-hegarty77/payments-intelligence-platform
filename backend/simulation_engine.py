import random
import uuid
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

CUSTOMER_COUNT = 24

# Fewer customers but higher activity per customer improves signal
CUSTOMERS = [f"CUST-{i:04d}" for i in range(1, CUSTOMER_COUNT + 1)]

# Per-customer activity/profile metadata
CUSTOMER_PROFILES = {}
for i, cid in enumerate(CUSTOMERS, start=1):
    activity_level = ["occasional", "regular", "frequent"][i % 3]
    min_gap, max_gap = {
        "occasional": (360, 720),
        "regular": (120, 360),
        "frequent": (45, 180),
    }[activity_level]
    CUSTOMER_PROFILES[cid] = {
        "activity_level": activity_level,
        "weight": 1,
        "baseline": 0.75 + (i % 8) * 0.12,
        "daily_limit": 650 + ((i * 137) % 850),
        "min_gap_minutes": min_gap,
        "max_gap_minutes": max_gap,
        "preferred_categories": [
            ["Groceries", "Coffee", "Transport"],
            ["Retail", "Food Delivery", "Entertainment"],
            ["Travel", "Hospitality", "Technology"],
        ][i % 3],
        "scenario": {
            0: "normal",
            1: "normal",
            2: "spend_escalation",
            3: "impossible_travel",
            4: "account_takeover",
        }.get(i % 10, "normal"),
        "transaction_count": 0,
        "next_transaction_at": None,
    }

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

ANOMALY_RATE = 0.0
SIMULATION_MINUTES_PER_TICK = 15

# assign home country and chance to transact abroad
COMMON_COUNTRIES = ['GB', 'IE', 'US', 'DE', 'FR', 'ES']
for cid, profile in CUSTOMER_PROFILES.items():
    # bias home country to GB/IE for most customers
    home = random.choice(['GB'] * 6 + ['IE'] * 3 + ['US', 'DE', 'FR', 'ES'])
    profile['home_country'] = home
    # small probability of choosing a country outside home during normal transactions
    profile['country_switch_prob'] = 0.03
    profile['next_transaction_at'] = SIMULATION_START + timedelta(
        minutes=random.randint(0, profile['max_gap_minutes'])
    )

def advance_clock(minutes=SIMULATION_MINUTES_PER_TICK):
    global simulation_time
    simulation_time += timedelta(minutes=minutes)
    return simulation_time


def build_transaction(merchant_name, customer_id, country, amount, timestamp=None):
    merchant=MERCHANTS[merchant_name]
    current_time=timestamp or simulation_time
    return Transaction(transaction_id=str(uuid.uuid4()),timestamp=current_time.isoformat(),merchant=merchant_name,country=country,amount=round(amount,2),customer_id=customer_id,merchant_category=merchant['category'],simulation_day=(current_time-SIMULATION_START).days,simulation_hour=current_time.hour)


def pick_customer_for_tick():
    urgent_customers = [
        customer_id
        for customer_id, profile in CUSTOMER_PROFILES.items()
        if profile.get("urgent_next_transaction")
    ]
    if urgent_customers:
        return urgent_customers[0]

    due_customers = [
        (customer_id, profile)
        for customer_id, profile in CUSTOMER_PROFILES.items()
        if profile["next_transaction_at"] <= simulation_time
    ]

    if due_customers:
        return random.choice(due_customers)[0]

    return random.choices(
        list(CUSTOMER_PROFILES),
        weights=[
            {"occasional": 1, "regular": 2, "frequent": 4}[profile["activity_level"]]
            for profile in CUSTOMER_PROFILES.values()
        ],
        k=1,
    )[0]


def pick_customer_merchant(profile):
    preferred = [
        merchant_name
        for merchant_name, merchant in MERCHANTS.items()
        if merchant["category"] in profile["preferred_categories"] and merchant["weight"] > 0
    ]
    return random.choice(preferred) if preferred and random.random() < 0.72 else pick_merchant()


def schedule_next_transaction(profile, current_time, urgent=False):
    if urgent:
        profile["next_transaction_at"] = current_time
        profile["urgent_next_transaction"] = True
        return

    profile["urgent_next_transaction"] = False
    profile["next_transaction_at"] = current_time + timedelta(
        minutes=random.randint(profile["min_gap_minutes"], profile["max_gap_minutes"])
    )


def generate_normal_transaction(customer_id=None, timestamp=None):
    current_time = timestamp or simulation_time
    customer_id = customer_id or pick_customer_for_tick()
    profile = CUSTOMER_PROFILES[customer_id]
    merchant_name = pick_customer_merchant(profile)
    merchant = MERCHANTS[merchant_name]

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
    if current_time.hour in merchant['busy_hours']:
        amount *= 1.08

    # clamp amount to reasonable merchant bounds
    amount = max(min_amt * 0.8, min(amount, max_amt * 1.2))
    return build_transaction(merchant_name, customer_id, country, amount, current_time)


def apply_customer_scenario(transaction, profile, current_time):
    count = profile["transaction_count"]
    scenario = profile["scenario"]

    # Scenarios begin only after a normal baseline has formed.
    if count < 12:
        return transaction

    if scenario == "spend_escalation" and count in (12, 13, 14):
        transaction.amount = round(transaction.amount * (3 + (count - 12) * 1.5), 2)

    if scenario == "impossible_travel" and count == 12:
        profile["travel_country"] = random.choice(
            [country for country in COMMON_COUNTRIES if country != transaction.country]
        )
        schedule_next_transaction(profile, current_time, urgent=True)

    if scenario == "impossible_travel" and count == 13:
        transaction.country = profile.get("travel_country", transaction.country)

    if scenario == "account_takeover" and count in (12, 13):
        candidates = [merchant for merchant, data in MERCHANTS.items() if data["high_risk"]]
        merchant_name = random.choice(candidates)
        merchant = MERCHANTS[merchant_name]
        transaction.merchant = merchant_name
        transaction.merchant_category = merchant["category"]
        transaction.country = random.choice(merchant["countries"])
        transaction.amount = round(random.uniform(*merchant["amount_range"]), 2)

    return transaction


def generate_transaction():
    current_time = advance_clock()
    customer_id = pick_customer_for_tick()
    profile = CUSTOMER_PROFILES[customer_id]
    transaction = generate_normal_transaction(customer_id, current_time)
    transaction = apply_customer_scenario(transaction, profile, current_time)
    profile["transaction_count"] += 1
    if profile["scenario"] == "impossible_travel" and profile["transaction_count"] == 13:
        schedule_next_transaction(profile, current_time, urgent=True)
    else:
        schedule_next_transaction(profile, current_time)
    return transaction
