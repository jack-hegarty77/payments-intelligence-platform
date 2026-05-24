from pydantic import BaseModel


class Payment(BaseModel):
    merchant: str
    amount: float
    country: str