from pydantic import BaseModel


class Payment(BaseModel):
    merchant: str
    amount: float
    country: str


class Transaction(BaseModel):
    transaction_id: str
    timestamp: str

    merchant: str
    country: str
    amount: float

    risk_score: int = 0

    alerts: list[str] = []
    actions: list[str] = []

    status: str = "APPROVED"