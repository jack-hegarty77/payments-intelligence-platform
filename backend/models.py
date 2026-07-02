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
    transaction_id: str = ""
    timestamp: str = ""

    merchant: str = ""
    country: str = ""
    amount: float = 0.0

    # -----------------------------
    # Simulation metadata
    # -----------------------------
    customer_id: str = "unknown"
    merchant_category: str = ""

    simulation_day: int = 0
    simulation_hour: int = 0

    # -----------------------------
    # New risk architecture
    # -----------------------------
    decision: str = "APPROVED"
    primary_reason: str = ""

    findings: List[Finding] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)

    # -----------------------------
    # Temporary compatibility layer
    # -----------------------------
    status: str = "APPROVED"
    alerts: List[str] = Field(default_factory=list)
    risk_score: int = 0