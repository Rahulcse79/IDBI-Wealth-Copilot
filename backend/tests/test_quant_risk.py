from app.quant.risk import RiskAnswers, assess_risk


def test_aggressive_profile():
    profile = assess_risk(
        RiskAnswers(age=26, horizon_years=20, loss_tolerance=5, occupation="salaried")
    )
    assert profile.bucket == "aggressive"
    assert profile.score > 65


def test_conservative_profile():
    profile = assess_risk(
        RiskAnswers(
            age=58,
            horizon_years=3,
            loss_tolerance=1,
            occupation="self_employed",
            dependents=3,
            has_emergency_fund=False,
        )
    )
    assert profile.bucket == "conservative"
    assert profile.score < 35


def test_score_is_clamped_and_matches_factor_sum():
    profile = assess_risk(RiskAnswers(age=35, horizon_years=7, loss_tolerance=3))
    raw = sum(f.contribution for f in profile.factors)
    assert 0 <= profile.score <= 100
    assert profile.score == max(0, min(100, raw))
