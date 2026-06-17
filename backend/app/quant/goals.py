"""Goal-based planning.

Given a goal and a risk bucket, compute the monthly SIP required to reach it, the
recommended allocation, and a gap analysis versus the customer's current trajectory.
Also supports "what-if" simulation of a different monthly contribution.

Math: standard future-value-of-annuity (ordinary annuity, end-of-period contributions),
with the monthly rate derived from the portfolio's blended annual return.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel

from app.models.domain import Goal
from app.quant.constants import INFLATION
from app.quant.portfolio import Portfolio, build_portfolio


def _monthly_rate(annual_rate: float) -> float:
    return (1 + annual_rate) ** (1 / 12) - 1


def _fv_annuity(monthly: float, r: float, n: int) -> float:
    """Future value of `monthly` invested at end of each period for `n` periods."""
    if r == 0:
        return monthly * n
    return monthly * (((1 + r) ** n - 1) / r)


def project_corpus(current_savings: float, monthly: float, annual_rate: float, years: float) -> float:
    """Project the corpus from current savings plus a fixed monthly contribution."""
    r = _monthly_rate(annual_rate)
    n = int(round(years * 12))
    return current_savings * (1 + r) ** n + _fv_annuity(monthly, r, n)


def _required_monthly(target: float, current_savings: float, annual_rate: float, years: float) -> float:
    r = _monthly_rate(annual_rate)
    n = int(round(years * 12))
    fv_current = current_savings * (1 + r) ** n
    remaining = target - fv_current
    if remaining <= 0:
        return 0.0
    if r == 0:
        return remaining / n
    return remaining * r / ((1 + r) ** n - 1)


class GoalPlan(BaseModel):
    label: str
    target_amount: int
    horizon_years: float
    current_savings: int
    bucket: str
    expected_return_pa: float
    required_monthly: int
    current_monthly_investment: int
    projected_with_current: int
    gap: int  # target - projected_with_current (positive = shortfall)
    on_track: bool
    additional_monthly_needed: int
    inflation_adjusted_target: int  # informational: target in today's money
    allocation: Portfolio
    product_ids: List[str]


def plan_goal(goal: Goal, bucket: str, current_monthly_investment: float = 0.0) -> GoalPlan:
    """Compute the plan for a single goal at a given risk bucket."""
    portfolio = build_portfolio(bucket)
    rate = portfolio.blended_return_pa

    required = _required_monthly(goal.target_amount, goal.current_savings, rate, goal.horizon_years)
    projected = project_corpus(goal.current_savings, current_monthly_investment, rate, goal.horizon_years)
    gap = goal.target_amount - projected
    real_target = goal.target_amount / ((1 + INFLATION) ** goal.horizon_years)

    return GoalPlan(
        label=goal.label,
        target_amount=goal.target_amount,
        horizon_years=goal.horizon_years,
        current_savings=goal.current_savings,
        bucket=bucket,
        expected_return_pa=round(rate, 4),
        required_monthly=int(round(required)),
        current_monthly_investment=int(round(current_monthly_investment)),
        projected_with_current=int(round(projected)),
        gap=int(round(gap)),
        on_track=gap <= 0,
        additional_monthly_needed=int(round(max(0.0, required - current_monthly_investment))),
        inflation_adjusted_target=int(round(real_target)),
        allocation=portfolio,
        product_ids=list(portfolio.product_ids),
    )


class Simulation(BaseModel):
    label: str
    monthly_contribution: int
    horizon_years: float
    expected_return_pa: float
    projected_corpus: int
    target_amount: int
    meets_target: bool
    surplus_or_gap: int  # projected - target


def simulate(goal: Goal, bucket: str, monthly_contribution: float) -> Simulation:
    """Project the outcome of a chosen monthly contribution (the 'what-if' lever)."""
    portfolio = build_portfolio(bucket)
    rate = portfolio.blended_return_pa
    projected = project_corpus(goal.current_savings, monthly_contribution, rate, goal.horizon_years)
    return Simulation(
        label=goal.label,
        monthly_contribution=int(round(monthly_contribution)),
        horizon_years=goal.horizon_years,
        expected_return_pa=round(rate, 4),
        projected_corpus=int(round(projected)),
        target_amount=goal.target_amount,
        meets_target=projected >= goal.target_amount,
        surplus_or_gap=int(round(projected - goal.target_amount)),
    )
