"""Financial assumptions for the prototype.

These are illustrative long-run assumptions for the Indian market, stated explicitly
so a reviewer can see and challenge them. They are NOT promises of return.
"""

from __future__ import annotations

# Long-run nominal expected returns per asset class (p.a.)
EQUITY_RETURN = 0.11  # broad Indian equity, long horizon
DEBT_RETURN = 0.067  # high-grade debt / fixed deposits
GOLD_RETURN = 0.075  # gold as a diversifier
HYBRID_RETURN = 0.09  # dynamic equity/debt blend

ASSET_RETURN = {
    "equity": EQUITY_RETURN,
    "debt": DEBT_RETURN,
    "gold": GOLD_RETURN,
    "hybrid": HYBRID_RETURN,
}

INFLATION = 0.06  # assumed long-run CPI for inflation-adjusted goal context
EMERGENCY_FUND_MONTHS = 6  # months of expenses kept liquid before investing

# Strategic asset allocation per risk bucket (weights sum to 1.0).
ALLOCATIONS = {
    "conservative": {"equity": 0.20, "debt": 0.70, "gold": 0.10},
    "balanced": {"equity": 0.50, "debt": 0.40, "gold": 0.10},
    "aggressive": {"equity": 0.75, "debt": 0.15, "gold": 0.10},
}

# Primary catalogue product representing each asset class in a model portfolio.
ASSET_CLASS_PRODUCT = {
    "equity": "MF-EQ-301",  # IDBI Nifty 50 Index Fund
    "debt": "IDBI-FD-001",  # IDBI Fixed Deposit
    "gold": "GOLD-SGB-401",  # Sovereign Gold Bond
}

RISK_BUCKETS = ("conservative", "balanced", "aggressive")
