from app.models.domain import Goal
from app.quant.goals import plan_goal, project_corpus, simulate


def test_required_sip_reaches_target():
    goal = Goal(label="house", target_amount=5_000_000, horizon_years=8, current_savings=0)
    plan = plan_goal(goal, "balanced")

    assert plan.required_monthly > 0
    # Investing exactly the required SIP should land within ~2% of the target.
    projected = project_corpus(0, plan.required_monthly, plan.expected_return_pa, 8)
    assert abs(projected - goal.target_amount) / goal.target_amount < 0.02


def test_current_savings_reduces_required_sip():
    goal_no_savings = Goal(label="car", target_amount=2_000_000, horizon_years=5)
    goal_with_savings = Goal(
        label="car", target_amount=2_000_000, horizon_years=5, current_savings=800_000
    )
    assert (
        plan_goal(goal_with_savings, "balanced").required_monthly
        < plan_goal(goal_no_savings, "balanced").required_monthly
    )


def test_higher_contribution_grows_corpus():
    goal = Goal(label="retirement", target_amount=10_000_000, horizon_years=20)
    low = simulate(goal, "aggressive", 10_000)
    high = simulate(goal, "aggressive", 20_000)
    assert high.projected_corpus > low.projected_corpus


def test_simulate_meets_target_flag():
    goal = Goal(label="house", target_amount=5_000_000, horizon_years=8)
    plan = plan_goal(goal, "balanced")
    result = simulate(goal, "balanced", plan.required_monthly)
    assert result.meets_target is True
