"""Product catalogue — the grounded source of truth for every recommendation.

These are representative IDBI-style products with *indicative* (never guaranteed)
returns. The copilot may only recommend a ``product_id`` that exists here; the
guardrail layer enforces this. Numbers are illustrative for the prototype.
"""

from __future__ import annotations

from typing import Dict, List

from app.models.domain import Product

_STD_DISCLAIMER = (
    "Indicative only and not guaranteed. Market-linked products are subject to market "
    "risk; read all scheme-related documents carefully before investing."
)
_FD_DISCLAIMER = (
    "Indicative interest rate; subject to change and applicable terms. Premature "
    "withdrawal may attract a penalty."
)

_RAW: List[Product] = [
    # ---- Debt / capital-protection ------------------------------------------------
    Product(
        product_id="IDBI-FD-001",
        name="IDBI Fixed Deposit",
        category="fixed_deposit",
        asset_class="debt",
        risk_level="low",
        indicative_return="6.8% p.a.",
        indicative_return_pa=0.068,
        min_investment=10000,
        lock_in="7 days to 10 years (flexible tenure)",
        description="Capital-safe term deposit for emergency funds and short-term goals "
        "with assured-style fixed tenure and predictable interest payouts.",
        disclaimer=_FD_DISCLAIMER,
    ),
    Product(
        product_id="IDBI-RD-002",
        name="IDBI Recurring Deposit",
        category="fixed_deposit",
        asset_class="debt",
        risk_level="low",
        indicative_return="6.6% p.a.",
        indicative_return_pa=0.066,
        min_investment=500,
        lock_in="6 months to 10 years",
        description="Disciplined monthly saving into a low-risk recurring deposit, ideal "
        "for building an emergency buffer or a near-term goal corpus.",
        disclaimer=_FD_DISCLAIMER,
    ),
    Product(
        product_id="IDBI-TAXFD-003",
        name="IDBI Tax-Saver Fixed Deposit",
        category="fixed_deposit",
        asset_class="debt",
        risk_level="low",
        indicative_return="6.9% p.a.",
        indicative_return_pa=0.069,
        min_investment=10000,
        lock_in="5 years (Section 80C)",
        description="Five-year tax-saving deposit eligible for Section 80C deduction; "
        "low risk with a fixed lock-in for tax planning.",
        disclaimer=_FD_DISCLAIMER,
    ),
    Product(
        product_id="MF-DEBT-101",
        name="IDBI Short Duration Debt Fund",
        category="mutual_fund",
        asset_class="debt",
        risk_level="low",
        indicative_return="7.0% p.a.",
        indicative_return_pa=0.070,
        min_investment=1000,
        lock_in="None (open-ended)",
        description="Open-ended debt mutual fund investing in short-duration bonds for "
        "stable, liquid returns better than a savings account for idle cash.",
        disclaimer=_STD_DISCLAIMER,
    ),
    # ---- Hybrid -------------------------------------------------------------------
    Product(
        product_id="MF-HYB-201",
        name="IDBI Balanced Advantage Fund",
        category="mutual_fund",
        asset_class="hybrid",
        risk_level="medium",
        indicative_return="9.5% p.a.",
        indicative_return_pa=0.095,
        min_investment=1000,
        lock_in="None (open-ended)",
        description="Dynamically allocates between equity and debt to balance growth and "
        "downside protection — a core holding for balanced investors.",
        disclaimer=_STD_DISCLAIMER,
    ),
    # ---- Equity -------------------------------------------------------------------
    Product(
        product_id="MF-EQ-301",
        name="IDBI Nifty 50 Index Fund",
        category="mutual_fund",
        asset_class="equity",
        risk_level="high",
        indicative_return="11.0% p.a.",
        indicative_return_pa=0.110,
        min_investment=500,
        lock_in="None (open-ended)",
        description="Low-cost index fund tracking the Nifty 50 for long-horizon wealth "
        "creation through systematic investment plans (SIPs).",
        disclaimer=_STD_DISCLAIMER,
    ),
    Product(
        product_id="MF-EQ-302",
        name="IDBI Flexi Cap Equity Fund",
        category="mutual_fund",
        asset_class="equity",
        risk_level="high",
        indicative_return="12.0% p.a.",
        indicative_return_pa=0.120,
        min_investment=500,
        lock_in="None (open-ended)",
        description="Actively managed diversified equity fund across large, mid and small "
        "caps for aggressive long-term growth goals such as retirement.",
        disclaimer=_STD_DISCLAIMER,
    ),
    Product(
        product_id="MF-ELSS-303",
        name="IDBI ELSS Tax-Saver Fund",
        category="mutual_fund",
        asset_class="equity",
        risk_level="high",
        indicative_return="11.5% p.a.",
        indicative_return_pa=0.115,
        min_investment=500,
        lock_in="3 years (Section 80C)",
        description="Equity-linked savings scheme combining long-term equity growth with "
        "Section 80C tax benefits and the shortest 80C lock-in.",
        disclaimer=_STD_DISCLAIMER,
    ),
    # ---- Gold ---------------------------------------------------------------------
    Product(
        product_id="GOLD-SGB-401",
        name="Sovereign Gold Bond (via IDBI)",
        category="govt_scheme",
        asset_class="gold",
        risk_level="medium",
        indicative_return="7.5% p.a.",
        indicative_return_pa=0.075,
        min_investment=5000,
        lock_in="8 years (exit option from year 5)",
        description="Government-backed gold bond paying periodic interest plus gold price "
        "appreciation — a portfolio diversifier and inflation hedge.",
        disclaimer=_STD_DISCLAIMER,
    ),
    # ---- Retirement / long-term ---------------------------------------------------
    Product(
        product_id="NPS-501",
        name="National Pension System (NPS) Tier-I",
        category="pension",
        asset_class="hybrid",
        risk_level="medium",
        indicative_return="9.0% p.a.",
        indicative_return_pa=0.090,
        min_investment=1000,
        lock_in="Until age 60 (retirement)",
        description="Low-cost, market-linked retirement account with additional Section "
        "80CCD(1B) tax benefit, suited to long-horizon retirement planning.",
        disclaimer=_STD_DISCLAIMER,
    ),
    Product(
        product_id="PPF-502",
        name="Public Provident Fund (PPF) via IDBI",
        category="govt_scheme",
        asset_class="debt",
        risk_level="low",
        indicative_return="7.1% p.a.",
        indicative_return_pa=0.071,
        min_investment=500,
        lock_in="15 years",
        description="Government-backed long-term savings with tax-free returns and "
        "Section 80C benefit; very low risk for conservative retirement saving.",
        disclaimer=_STD_DISCLAIMER,
    ),
    # ---- Protection ---------------------------------------------------------------
    Product(
        product_id="INS-TERM-601",
        name="IDBI Term Life Cover",
        category="insurance",
        asset_class="protection",
        risk_level="low",
        indicative_return="N/A (protection, not investment)",
        indicative_return_pa=0.0,
        min_investment=6000,
        lock_in="Policy term",
        description="Pure-protection term life insurance providing a large cover at low "
        "premium to protect dependents — recommended before investing for goals.",
        disclaimer="Protection product. Premiums and cover are subject to underwriting "
        "and policy terms.",
    ),
    Product(
        product_id="INS-HEALTH-602",
        name="IDBI Health Shield",
        category="insurance",
        asset_class="protection",
        risk_level="low",
        indicative_return="N/A (protection, not investment)",
        indicative_return_pa=0.0,
        min_investment=8000,
        lock_in="1 year (renewable)",
        description="Comprehensive health insurance to protect savings from medical "
        "emergencies — a foundation of any financial plan.",
        disclaimer="Protection product. Premiums and cover are subject to underwriting "
        "and policy terms.",
    ),
]

CATALOGUE: List[Product] = list(_RAW)
_BY_ID: Dict[str, Product] = {p.product_id: p for p in CATALOGUE}
_VALID_NAMES = {p.name for p in CATALOGUE}


def all_products() -> List[Product]:
    """Return the full product catalogue."""
    return list(CATALOGUE)


def get_product(product_id: str) -> Product:
    """Return a product by id, or raise ``KeyError`` if it is not in the catalogue."""
    return _BY_ID[product_id]


def is_valid_product_name(name: str) -> bool:
    """True if ``name`` exactly matches a catalogue product (used by the guardrail)."""
    return name in _VALID_NAMES


def valid_product_names() -> List[str]:
    """All catalogue product names — the allow-list the guardrail grounds against."""
    return sorted(_VALID_NAMES)
