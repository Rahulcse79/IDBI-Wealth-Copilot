"""Risk profiling.

Maps a short questionnaire (plus a few customer attributes) to a 0-100 risk-capacity
score and a bucket. The scoring rubric is explicit and additive so every point is
explainable — important for a bank's compliance review.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

# Map occupation -> income-stability score (1 = volatile, 5 = very stable).
_OCCUPATION_STABILITY = {"salaried": 4, "business": 3, "self_employed": 2}


class RiskAnswers(BaseModel):
    """Inputs to risk profiling. Most have safe defaults so a partial answer still scores."""

    age: int = 35
    horizon_years: float = 7
    loss_tolerance: int = Field(default=3, ge=1, le=5)  # 1 = panic-sell, 5 = stay invested
    occupation: str = "salaried"
    income_stability: Optional[int] = None  # 1-5; falls back to occupation mapping
    dependents: int = 0
    has_emergency_fund: bool = True


class RiskFactor(BaseModel):
    factor: str
    contribution: int  # signed points this factor added to the score
    note: str


class RiskProfile(BaseModel):
    score: int  # 0-100 risk capacity
    bucket: str  # conservative | balanced | aggressive
    factors: List[RiskFactor]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def assess_risk(answers: RiskAnswers) -> RiskProfile:
    """Compute a risk-capacity score and bucket from the questionnaire."""
    factors: List[RiskFactor] = []
    base = 50
    factors.append(RiskFactor(factor="baseline", contribution=base, note="Neutral starting point"))

    age_pts = int(_clamp((40 - answers.age) * 0.6, -18, 18))
    factors.append(
        RiskFactor(
            factor="age",
            contribution=age_pts,
            note=f"Age {answers.age}: a longer earning runway raises risk capacity",
        )
    )

    horizon_pts = int(_clamp((answers.horizon_years - 5) * 2, -16, 20))
    factors.append(
        RiskFactor(
            factor="horizon",
            contribution=horizon_pts,
            note=f"{answers.horizon_years:g}-year horizon: more time absorbs market swings",
        )
    )

    tol_pts = (answers.loss_tolerance - 3) * 8
    factors.append(
        RiskFactor(
            factor="loss_tolerance",
            contribution=tol_pts,
            note=f"Loss tolerance {answers.loss_tolerance}/5 (behavioural willingness to stay invested)",
        )
    )

    stability = answers.income_stability or _OCCUPATION_STABILITY.get(answers.occupation, 3)
    stab_pts = (stability - 3) * 4
    factors.append(
        RiskFactor(
            factor="income_stability",
            contribution=stab_pts,
            note=f"Income stability {stability}/5 ({answers.occupation})",
        )
    )

    dep_pts = -answers.dependents * 2
    factors.append(
        RiskFactor(
            factor="dependents",
            contribution=dep_pts,
            note=f"{answers.dependents} dependent(s): higher obligations reduce risk capacity",
        )
    )

    ef_pts = 5 if answers.has_emergency_fund else -8
    factors.append(
        RiskFactor(
            factor="emergency_fund",
            contribution=ef_pts,
            note="Emergency fund in place" if answers.has_emergency_fund else "No emergency buffer",
        )
    )

    score = int(_clamp(sum(f.contribution for f in factors), 0, 100))
    bucket = "conservative" if score < 35 else "balanced" if score <= 65 else "aggressive"
    return RiskProfile(score=score, bucket=bucket, factors=factors)
