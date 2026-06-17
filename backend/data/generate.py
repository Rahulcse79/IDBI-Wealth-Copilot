"""Deterministic synthetic data generator.

Run as a module from the ``backend/`` directory::

    python -m data.generate --seed 20260617 --n-customers 40 --months 18

Produces ``customers.json`` and ``transactions.json`` under ``data/synthetic``.
Generation is fully seeded so results reproduce exactly. Three hand-tuned demo
personas (``CUST-DEMO-1..3``) are always included so the three demo flows in
``context/05_BUILD_REQUIREMENTS.md`` reliably have something to find.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

_OUT_DIR = Path(__file__).resolve().parent / "synthetic"
_END = date(2026, 6, 1)  # data ends here, deterministically

_FIRST_NAMES = [
    "Aarav", "Meera", "Rohan", "Priya", "Karan", "Ananya", "Vikram", "Isha",
    "Arjun", "Neha", "Sanjay", "Divya", "Rahul", "Pooja", "Aditya", "Kavya",
]
_LAST_NAMES = ["Sharma", "Iyer", "Verma", "Nair", "Gupta", "Reddy", "Mehta", "Khan"]
_CITIES = ["Mumbai", "Bengaluru", "Delhi", "Pune", "Hyderabad", "Chennai", "Ahmedabad"]
_OCCUPATIONS = ["salaried", "self_employed", "business"]


@dataclass
class Persona:
    """Parameters that drive a customer's transaction synthesis."""

    customer_id: str
    name: str
    age: int
    city: str
    occupation: str
    monthly_income: int
    rent: int
    emi: int
    emi_merchant: str
    monthly_sip: int  # how much they already invest each month
    start_balance: float
    discretionary_ratio: float  # share of income spent on lifestyle
    dependents: int = 0
    existing_investments: List[Dict[str, object]] = field(default_factory=list)


def _add_months(d: date, delta: int) -> date:
    month_index = (d.year * 12 + (d.month - 1)) + delta
    return date(month_index // 12, month_index % 12 + 1, 1)


def _synthesize_transactions(persona: Persona, months: int, rng: random.Random) -> List[dict]:
    """Build a month-by-month transaction ledger with a reconciling running balance."""
    txns: List[dict] = []
    balance = persona.start_balance
    seq = 0
    start = _add_months(_END, -(months - 1))

    def push(d: date, amount: float, ttype: str, merchant: str, category: str) -> None:
        nonlocal balance, seq
        balance = round(balance + amount, 2)
        seq += 1
        txns.append(
            {
                "txn_id": f"{persona.customer_id}-T{seq:04d}",
                "customer_id": persona.customer_id,
                "date": d.isoformat(),
                "amount": round(amount, 2),
                "type": ttype,
                "merchant": merchant,
                "category": category,
                "balance_after": balance,
            }
        )

    for m in range(months):
        month = _add_months(start, m)
        y, mo = month.year, month.month

        push(date(y, mo, 1), persona.monthly_income, "ach", "Employer Payroll", "salary")
        if persona.rent:
            push(date(y, mo, 3), -persona.rent, "neft", "Landlord", "rent")
        if persona.emi:
            push(date(y, mo, 5), -persona.emi, "ach", persona.emi_merchant, "emi")

        discretionary = persona.monthly_income * persona.discretionary_ratio
        push(date(y, mo, 8), -round(discretionary * 0.45, 2), "card", "BigBasket", "groceries")
        push(date(y, mo, 14), -round(discretionary * 0.20, 2), "upi", "Electricity Board", "utilities")
        push(date(y, mo, 19), -round(discretionary * 0.25, 2), "card", "Zomato", "dining")
        push(date(y, mo, 24), -round(discretionary * 0.10, 2), "upi", "Netflix", "entertainment")

        if persona.monthly_sip:
            push(date(y, mo, 6), -persona.monthly_sip, "ach", "IDBI Mutual Fund SIP", "investment")

        if mo in (3, 6, 9, 12):  # quarterly savings interest
            push(date(y, mo, 28), round(balance * 0.0085, 2), "interest", "IDBI Bank", "interest")

    return txns


def _persona_to_customer(p: Persona, txns: List[dict]) -> dict:
    savings_balance = txns[-1]["balance_after"] if txns else p.start_balance
    return {
        "customer_id": p.customer_id,
        "name": p.name,
        "age": p.age,
        "city": p.city,
        "occupation": p.occupation,
        "monthly_income": p.monthly_income,
        "dependents": p.dependents,
        "accounts": [{"kind": "savings", "balance": round(savings_balance, 2)}],
        "existing_investments": p.existing_investments,
        "risk_appetite": None,
    }


def _demo_personas() -> List[Persona]:
    """Three curated personas, one per demo flow."""
    return [
        # Flow 1 — idle cash + costly debt. Low SIP, high idle balance, personal-loan EMI.
        Persona(
            customer_id="CUST-DEMO-1",
            name="Aarav Sharma",
            age=28,
            city="Bengaluru",
            occupation="salaried",
            monthly_income=95000,
            rent=22000,
            emi=8500,
            emi_merchant="Personal Loan EMI",
            monthly_sip=0,
            start_balance=210000,
            discretionary_ratio=0.32,
            dependents=0,
            existing_investments=[{"kind": "fixed_deposit", "value": 50000}],
        ),
        # Flow 2 — goal planning. Disciplined saver with a house-goal corpus started.
        Persona(
            customer_id="CUST-DEMO-2",
            name="Meera Iyer",
            age=34,
            city="Mumbai",
            occupation="salaried",
            monthly_income=140000,
            rent=38000,
            emi=0,
            emi_merchant="",
            monthly_sip=15000,
            start_balance=180000,
            discretionary_ratio=0.30,
            dependents=1,
            existing_investments=[
                {"kind": "mutual_fund", "value": 600000},
                {"kind": "fixed_deposit", "value": 200000},
            ],
        ),
        # Flow 3 — grounded recommendations / retirement context.
        Persona(
            customer_id="CUST-DEMO-3",
            name="Rohan Verma",
            age=45,
            city="Pune",
            occupation="self_employed",
            monthly_income=180000,
            rent=0,
            emi=32000,
            emi_merchant="Home Loan EMI",
            monthly_sip=20000,
            start_balance=320000,
            discretionary_ratio=0.34,
            dependents=2,
            existing_investments=[
                {"kind": "mutual_fund", "value": 1200000},
                {"kind": "pension", "value": 450000},
            ],
        ),
    ]


def _random_persona(i: int, rng: random.Random) -> Persona:
    income = rng.choice([35000, 55000, 75000, 110000, 160000, 240000])
    occupation = rng.choice(_OCCUPATIONS)
    has_emi = rng.random() < 0.5
    invests = rng.random() < 0.55
    return Persona(
        customer_id=f"CUST-{i:05d}",
        name=f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}",
        age=rng.randint(23, 60),
        city=rng.choice(_CITIES),
        occupation=occupation,
        monthly_income=income,
        rent=rng.choice([0, int(income * 0.22), int(income * 0.28)]),
        emi=int(income * rng.uniform(0.08, 0.25)) if has_emi else 0,
        emi_merchant=rng.choice(["Home Loan EMI", "Auto Loan EMI", "Personal Loan EMI"]),
        monthly_sip=int(income * rng.uniform(0.05, 0.18)) if invests else 0,
        start_balance=income * rng.uniform(1.5, 6.0),
        discretionary_ratio=rng.uniform(0.25, 0.45),
        dependents=rng.randint(0, 4),
    )


def generate(seed: int, n_customers: int, months: int) -> Dict[str, List[dict]]:
    """Generate the full dataset (demo personas first, then random customers)."""
    rng = random.Random(seed)
    customers: List[dict] = []
    transactions: List[dict] = []

    personas = _demo_personas()
    personas += [_random_persona(i, rng) for i in range(1, n_customers + 1)]

    for p in personas:
        txns = _synthesize_transactions(p, months, rng)
        customers.append(_persona_to_customer(p, txns))
        transactions.extend(txns)

    return {"customers": customers, "transactions": transactions}


def write(dataset: Dict[str, List[dict]], out_dir: Optional[Path] = None) -> Path:
    out = out_dir or _OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    (out / "customers.json").write_text(json.dumps(dataset["customers"], indent=2))
    (out / "transactions.json").write_text(json.dumps(dataset["transactions"], indent=2))
    # Commit just the three demo personas so the repo is demoable without regenerating.
    demo = [c for c in dataset["customers"] if c["customer_id"].startswith("CUST-DEMO")]
    (out / "demo_customers.json").write_text(json.dumps(demo, indent=2))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic Wealth Copilot data.")
    parser.add_argument("--seed", type=int, default=20260617)
    parser.add_argument("--n-customers", type=int, default=40)
    parser.add_argument("--months", type=int, default=18)
    args = parser.parse_args()

    dataset = generate(args.seed, args.n_customers, args.months)
    out = write(dataset)
    print(
        f"Wrote {len(dataset['customers'])} customers and "
        f"{len(dataset['transactions'])} transactions to {out}"
    )


if __name__ == "__main__":
    main()
