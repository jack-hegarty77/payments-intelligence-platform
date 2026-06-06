from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import Payment
from risk_engine import calculate_risk

app = FastAPI(title="Payments Intelligence API")

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
    return calculate_risk(payment)