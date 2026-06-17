from app.models.domain import Customer, Transaction
from app.quant.insights import analyze
from data.generate import generate


def _demo_customer(customer_id):
    dataset = generate(seed=20260617, n_customers=0, months=18)
    customer = next(c for c in dataset["customers"] if c["customer_id"] == customer_id)
    txns = [t for t in dataset["transactions"] if t["customer_id"] == customer_id]
    return Customer(**customer), [Transaction(**t) for t in txns]


def test_idle_cash_and_costly_debt_flagged_for_aarav():
    customer, txns = _demo_customer("CUST-DEMO-1")
    insights = analyze(customer, txns)

    # Aarav earns ~95k, has a personal-loan EMI and lets cash pile up.
    assert 90_000 <= insights.estimated_monthly_income <= 100_000
    assert insights.monthly_costly_debt == 8500
    assert insights.idle_cash > 0

    action_ids = {a.id for a in insights.actions}
    assert "clear_costly_debt" in action_ids
    assert "deploy_idle_cash" in action_ids


def test_savings_rate_between_zero_and_one():
    customer, txns = _demo_customer("CUST-DEMO-2")
    insights = analyze(customer, txns)
    assert 0.0 <= insights.savings_rate <= 1.0
    assert insights.top_spend_categories  # non-empty
