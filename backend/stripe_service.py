import os
import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def get_recent_payments(limit=10):
    payments = stripe.PaymentIntent.list(limit=limit)

    return payments.data