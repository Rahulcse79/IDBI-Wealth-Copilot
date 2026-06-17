"""Core domain entities.

These mirror the schemas in ``context/03_DATASET_SPECIFICATIONS.md`` and are the
single source of truth that crosses module boundaries (no loose dicts).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------


class Account(BaseModel):
    kind: str  # savings | current
    balance: float


class Investment(BaseModel):
    kind: str  # fixed_deposit | mutual_fund | insurance | ...
    value: float


class Customer(BaseModel):
    customer_id: str
    name: str
    age: int
    city: str
    occupation: str  # salaried | self_employed | business
    monthly_income: Optional[int] = None  # estimated; may be unknown
    dependents: int = 0
    accounts: List[Account] = Field(default_factory=list)
    existing_investments: List[Investment] = Field(default_factory=list)
    risk_appetite: Optional[str] = None  # filled after the questionnaire

    @property
    def total_savings_balance(self) -> float:
        return sum(a.balance for a in self.accounts if a.kind == "savings")


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


class Transaction(BaseModel):
    txn_id: str
    customer_id: str
    date: str  # ISO date
    amount: float  # debit negative, credit positive
    type: str  # upi | card | neft | ach | cash | interest
    merchant: str
    category: str  # salary | rent | groceries | emi | investment | ...
    balance_after: float


# ---------------------------------------------------------------------------
# Products (the RAG ground truth)
# ---------------------------------------------------------------------------


class Product(BaseModel):
    product_id: str
    name: str
    category: str  # fixed_deposit | mutual_fund | insurance | pension | govt_scheme
    asset_class: str  # equity | debt | gold | hybrid | protection
    risk_level: str  # low | medium | high
    indicative_return: str  # ALWAYS indicative, never guaranteed
    indicative_return_pa: float  # numeric form for the quant engine
    min_investment: int
    lock_in: str
    description: str
    disclaimer: str


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------


class Goal(BaseModel):
    label: str
    target_amount: int
    horizon_years: float
    current_savings: int = 0
