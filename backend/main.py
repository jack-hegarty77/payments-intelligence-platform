from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import Payment, Transaction
from stripe_service import get_recent_payments

import asyncio

from transaction_generator import generate_transaction
from risk_engine import assess_transaction

app = FastAPI(title="Payments Intelligence API")

transactions_store = []


async def transaction_stream():
    while True:
        tx = generate_transaction()

        tx = assess_transaction(tx)

        transactions_store.append(
            tx.model_dump()
        )

        # Keep only latest 100 transactions
        if len(transactions_store) > 100:
            transactions_store.pop(0)

        await asyncio.sleep(1)


@app.on_event("startup")
async def start_stream():
    asyncio.create_task(transaction_stream())


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"status": "running"}


@app.post("/payments/check")
def check_payment(payment: Payment):

    transaction = Transaction(
        transaction_id="manual-check",
        timestamp="manual-check",
        merchant=payment.merchant,
        country=payment.country,
        amount=payment.amount,
    )

    return assess_transaction(
        transaction
    ).model_dump()


@app.get("/transactions/generate")
def generate_transactions(count: int = 10):

    transactions = []

    for _ in range(count):
        transactions.append(
            generate_transaction()
        )

    return transactions


@app.get("/stripe/payments")
def stripe_payments():

    payments = get_recent_payments()

    return [
        {
            "id": p.id,
            "amount": p.amount / 100,
            "currency": p.currency,
            "status": p.status,
        }
        for p in payments
    ]


@app.get("/transactions/live")
def get_live_transactions():
    return transactions_store[-20:]