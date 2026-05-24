from fastapi import FastAPI
from models import Payment
from risk_engine import calculate_risk

app = FastAPI(title="Payments Intelligence API")


@app.get("/")
def home():
    return {"status": "running"}


@app.post("/payments/check")
def check_payment(payment: Payment):
    return calculate_risk(payment)