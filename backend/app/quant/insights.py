"""Behavioural insights from transaction data.

Estimates income, savings rate, idle cash and costly debt from a customer's
transaction ledger, and produces a ranked list of "next best actions" — each with
the exact numbers behind it, so every nudge is explainable.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from pydantic import BaseModel

from app.models.domain import Customer, Transaction
from app.quant.constants import EMERGENCY_FUND_MONTHS

# Merchants whose EMIs we treat as high-interest (costly) debt.
_COSTLY_DEBT_MARKERS = ("personal loan", "credit card")
# Idle cash above this multiple of the emergency buffer is worth flagging.
_IDLE_FLAG_FLOOR = 50000


class NextBestAction(BaseModel):
    id: str
    title: str
    detail: str
    impact: str  # high | medium | low
    evidence: Dict[str, float]


class FinancialInsights(BaseModel):
    customer_id: str
    months_observed: int
    estimated_monthly_income: int
    estimated_monthly_expenses: int
    savings_rate: float  # 0..1
    savings_balance: int
    emergency_fund_target: int
    idle_cash: int
    monthly_costly_debt: int
    top_spend_categories: List[Dict[str, Any]]
    actions: List[NextBestAction]


def _month_key(iso_date: str) -> str:
    return iso_date[:7]  # YYYY-MM


def analyze(customer: Customer, transactions: List[Transaction]) -> FinancialInsights:
    """Derive insights and ranked actions for a customer."""
    months = sorted({_month_key(t.date) for t in transactions})
    n_months = max(1, len(months))

    salary_by_month: Dict[str, float] = defaultdict(float)
    spend_by_month: Dict[str, float] = defaultdict(float)
    spend_by_category: Dict[str, float] = defaultdict(float)
    invests = False
    costly_debt_monthly = 0.0

    for t in transactions:
        mk = _month_key(t.date)
        if t.category == "salary" and t.amount > 0:
            salary_by_month[mk] += t.amount
        elif t.category == "investment":
            invests = True
        elif t.amount < 0:  # an expense (rent, emi, groceries, ...)
            spend = -t.amount
            spend_by_month[mk] += spend
            spend_by_category[t.category] += spend
            if t.category == "emi" and any(m in t.merchant.lower() for m in _COSTLY_DEBT_MARKERS):
                costly_debt_monthly = max(costly_debt_monthly, -t.amount)

    income = (sum(salary_by_month.values()) / n_months) if salary_by_month else (
        customer.monthly_income or 0.0
    )
    expenses = (sum(spend_by_month.values()) / n_months) if spend_by_month else 0.0
    savings_rate = (income - expenses) / income if income > 0 else 0.0

    savings_balance = customer.total_savings_balance
    emergency_target = expenses * EMERGENCY_FUND_MONTHS
    idle_cash = max(0.0, savings_balance - emergency_target)

    top_categories = sorted(spend_by_category.items(), key=lambda kv: kv[1], reverse=True)[:3]
    top_spend = [
        {"category": name, "monthly_amount": round(total / n_months)} for name, total in top_categories
    ]

    actions = _rank_actions(
        costly_debt_monthly=costly_debt_monthly,
        idle_cash=idle_cash,
        invests=invests,
        savings_rate=savings_rate,
        income=income,
        has_protection=any(i.kind == "insurance" for i in customer.existing_investments),
    )

    return FinancialInsights(
        customer_id=customer.customer_id,
        months_observed=n_months,
        estimated_monthly_income=int(round(income)),
        estimated_monthly_expenses=int(round(expenses)),
        savings_rate=round(savings_rate, 3),
        savings_balance=int(round(savings_balance)),
        emergency_fund_target=int(round(emergency_target)),
        idle_cash=int(round(idle_cash)),
        monthly_costly_debt=int(round(costly_debt_monthly)),
        top_spend_categories=top_spend,
        actions=actions,
    )


def _rank_actions(
    *,
    costly_debt_monthly: float,
    idle_cash: float,
    invests: bool,
    savings_rate: float,
    income: float,
    has_protection: bool,
) -> List[NextBestAction]:
    actions: List[NextBestAction] = []

    if costly_debt_monthly > 0:
        actions.append(
            NextBestAction(
                id="clear_costly_debt",
                title="Clear high-interest debt first",
                detail=(
                    "You have a high-interest EMI. Paying it down typically beats the "
                    "after-tax return of most investments, so prioritise it before investing."
                ),
                impact="high",
                evidence={"monthly_costly_debt": round(costly_debt_monthly)},
            )
        )

    if idle_cash >= _IDLE_FLAG_FLOOR:
        actions.append(
            NextBestAction(
                id="deploy_idle_cash",
                title="Put idle savings to work",
                detail=(
                    "A large balance is sitting idle in your savings account beyond your "
                    "emergency buffer. Moving it into a low-risk debt option can earn more "
                    "without locking it away."
                ),
                impact="high",
                evidence={"idle_cash": round(idle_cash)},
            )
        )

    if not has_protection and income > 0:
        actions.append(
            NextBestAction(
                id="get_protection",
                title="Protect your plan with insurance",
                detail=(
                    "No life or health cover was detected. A low-cost term and health policy "
                    "protects your savings from a single emergency — the foundation of a plan."
                ),
                impact="medium",
                evidence={"estimated_monthly_income": round(income)},
            )
        )

    if not invests and savings_rate > 0:
        actions.append(
            NextBestAction(
                id="start_sip",
                title="Start a monthly SIP",
                detail=(
                    "You are saving every month but not investing it. A systematic investment "
                    "plan turns that surplus into long-term growth."
                ),
                impact="medium",
                evidence={"savings_rate": round(savings_rate, 3)},
            )
        )

    return actions
