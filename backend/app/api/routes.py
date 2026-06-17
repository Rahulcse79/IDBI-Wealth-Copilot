"""FastAPI routes.

The quant endpoints (insights, risk, goal-plan, simulate, products) run fully offline on
synthetic data — they demo the engine without an API key. ``/api/chat`` adds the
conversational copilot and needs an Anthropic credential.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.agent.orchestrator import Copilot, CopilotConfigError
from app.config import anthropic_key_available, get_settings
from app.models.api import (
    ChatRequest,
    ChatResponse,
    ConfigResponse,
    CustomerSummary,
    GoalRequest,
    RiskRequest,
    SimulateRequest,
)
from app.models.domain import Customer, Goal
from app.providers import get_provider
from app.quant.goals import plan_goal, simulate
from app.quant.insights import FinancialInsights, analyze
from app.quant.risk import RiskAnswers, RiskProfile, assess_risk
from app.rag import get_retriever

router = APIRouter(prefix="/api")
_copilot = Copilot()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/config", response_model=ConfigResponse)
def config() -> ConfigResponse:
    settings = get_settings()
    return ConfigResponse(
        copilot_available=anthropic_key_available(),
        model=settings.model,
        data_provider=settings.data_provider,
    )


@router.get("/customers", response_model=list)
def list_customers() -> list:
    provider = get_provider()
    return [
        CustomerSummary(
            customer_id=c.customer_id,
            name=c.name,
            age=c.age,
            city=c.city,
            occupation=c.occupation,
        )
        for c in provider.list_customers()
    ]


@router.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: str) -> Customer:
    try:
        return get_provider().get_customer(customer_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")


@router.get("/customers/{customer_id}/insights", response_model=FinancialInsights)
def customer_insights(customer_id: str) -> FinancialInsights:
    provider = get_provider()
    try:
        customer = provider.get_customer(customer_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    txns = provider.get_transactions(customer_id, months=18)
    return analyze(customer, txns)


@router.post("/risk", response_model=RiskProfile)
def risk(req: RiskRequest) -> RiskProfile:
    provider = get_provider()
    try:
        customer = provider.get_customer(req.customer_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Customer {req.customer_id} not found")
    answers = RiskAnswers(
        age=customer.age,
        occupation=customer.occupation,
        dependents=customer.dependents,
        horizon_years=req.horizon_years,
        loss_tolerance=req.loss_tolerance,
        has_emergency_fund=req.has_emergency_fund,
    )
    return assess_risk(answers)


def _resolve_bucket(customer_id: str, bucket, horizon_years: float) -> str:
    if bucket:
        return bucket
    provider = get_provider()
    customer = provider.get_customer(customer_id)
    answers = RiskAnswers(
        age=customer.age,
        occupation=customer.occupation,
        dependents=customer.dependents,
        horizon_years=horizon_years,
    )
    return assess_risk(answers).bucket


@router.post("/goal-plan")
def goal_plan(req: GoalRequest):
    try:
        bucket = _resolve_bucket(req.customer_id, req.bucket, req.horizon_years)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Customer {req.customer_id} not found")
    goal = Goal(
        label=req.label,
        target_amount=req.target_amount,
        horizon_years=req.horizon_years,
        current_savings=req.current_savings,
    )
    return plan_goal(goal, bucket)


@router.post("/simulate")
def simulate_goal(req: SimulateRequest):
    try:
        bucket = _resolve_bucket(req.customer_id, req.bucket, req.horizon_years)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Customer {req.customer_id} not found")
    goal = Goal(
        label=req.label,
        target_amount=req.target_amount,
        horizon_years=req.horizon_years,
        current_savings=req.current_savings,
    )
    return simulate(goal, bucket, req.monthly_contribution)


@router.get("/products")
def products(
    q: str = Query(default=""),
    max_risk: str = Query(default=None),
    asset_class: str = Query(default=None),
):
    results = get_retriever().search(q, max_risk=max_risk, asset_class=asset_class, top_k=8)
    return {"products": [{**p.model_dump(), "relevance": s} for p, s in results]}


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    provider = get_provider()
    try:
        customer = provider.get_customer(req.customer_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Customer {req.customer_id} not found")
    try:
        reply = _copilot.run(
            customer_id=req.customer_id,
            customer_name=customer.name,
            history=[t.model_dump() for t in req.history],
            user_message=req.message,
        )
    except CopilotConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return ChatResponse(**reply.model_dump())
