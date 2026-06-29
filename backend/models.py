from pydantic import BaseModel, Field
from typing import List


# =====================================================
# INPUT MODEL (used by /payments/check)
# =====================================================

class Payment(BaseModel):
    merchant: str
    country: str
    amount: float


# =====================================================
# RISK FINDING MODEL
# =====================================================

class Finding(BaseModel):
    detector: str
    severity: str
    title: str
    description: str


# =====================================================
# CORE TRANSACTION MODEL
# =====================================================

class Transaction(BaseModel):
    transaction_id: str
    timestamp: str

    merchant: str
    country: str
    amount: float

    # -----------------------------
    # NEW ARCHITECTURE
    # -----------------------------
    decision: str = "APPROVED"
    primary_reason: str = ""

    findings: List[Finding] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)

    # -----------------------------
    # TEMP COMPAT LAYER
    # -----------------------------
    status: str = "APPROVED"
    alerts: List[str] = Field(default_factory=list)
    risk_score: int = 0