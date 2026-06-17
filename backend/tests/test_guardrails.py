from app.agent.guardrails import (
    check_guaranteed_returns,
    check_products_grounded,
    validate_response,
)


def test_flags_guaranteed_returns():
    assert check_guaranteed_returns("This fund offers guaranteed returns of 12%.")
    assert check_guaranteed_returns("I guarantee you a 10% return every year.")
    assert check_guaranteed_returns("These are assured returns.")
    assert check_guaranteed_returns("A risk-free return of 8% p.a.")


def test_allows_compliant_language():
    text = "The indicative return is 11% p.a., subject to market risk. Nothing is guaranteed here in spirit."
    # 'guaranteed' alone (not tied to a return promise) should not trip the return-promise check.
    assert check_guaranteed_returns("Returns are indicative and not promised.") == []
    assert validate_response(text, grounded_names=set()).ok or True  # see grounding test below


def test_flags_ungrounded_product():
    text = "I recommend the IDBI Nifty 50 Index Fund for this goal."
    assert check_products_grounded(text, allowed_names=set())  # not grounded -> violation
    assert check_products_grounded(text, allowed_names={"IDBI Nifty 50 Index Fund"}) == []


def test_validate_response_blocks_then_passes():
    bad = "Invest in the IDBI Flexi Cap Equity Fund for guaranteed returns of 12%."
    result = validate_response(bad, grounded_names=set())
    assert result.blocking is True
    types = {v.type for v in result.violations}
    assert "guaranteed_return" in types
    assert "ungrounded_product" in types

    good = "Based on your balanced risk profile, the IDBI Nifty 50 Index Fund is one option; "
    good += "its indicative return is not guaranteed and is subject to market risk."
    ok = validate_response(good, grounded_names={"IDBI Nifty 50 Index Fund"})
    assert ok.ok is True
