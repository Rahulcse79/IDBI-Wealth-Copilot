"""Agent tools — the only way the copilot can touch data or run calculations.

Each tool is a typed function the LLM may call. The :class:`ToolExecutor` dispatches a
tool call to the provider / quant engine / retriever, returns a JSON-serialisable result,
and tracks which catalogue products have been *grounded* this turn so the guardrail can
verify the final answer only cites products the model actually looked up.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

from app.models.domain import Goal
from app.providers import get_provider
from app.quant.goals import plan_goal, simulate
from app.quant.insights import analyze
from app.quant.risk import RiskAnswers, assess_risk
from app.rag import get_retriever

# Tool schemas advertised to Claude. Descriptions are prescriptive about *when* to call.
TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_customer_profile",
        "description": "Fetch the customer's profile: age, occupation, income, dependents, "
        "balances and existing investments. Call this first to ground any advice in who "
        "the customer is.",
        "input_schema": {
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_next_best_actions",
        "description": "Analyse the customer's transactions to estimate income, savings rate, "
        "idle cash and high-interest debt, and return ranked next-best-actions with the "
        "numbers behind them. Call this when the customer asks where to start or what to "
        "improve.",
        "input_schema": {
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"],
        },
    },
    {
        "name": "assess_risk",
        "description": "Compute the customer's risk-capacity score and bucket "
        "(conservative/balanced/aggressive). Call this before recommending an allocation. "
        "Optional questionnaire fields refine the score.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "horizon_years": {"type": "number"},
                "loss_tolerance": {"type": "integer", "minimum": 1, "maximum": 5},
                "has_emergency_fund": {"type": "boolean"},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "plan_goal",
        "description": "Compute the monthly SIP required to reach a financial goal, the "
        "recommended allocation (grounded in real products), and a gap analysis vs the "
        "customer's current investing. Call this for any goal like a house, education or "
        "retirement.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "label": {"type": "string", "description": "Goal name, e.g. 'house'"},
                "target_amount": {"type": "integer", "description": "Target corpus in rupees"},
                "horizon_years": {"type": "number"},
                "current_savings": {"type": "integer", "description": "Amount already set aside"},
                "bucket": {
                    "type": "string",
                    "enum": ["conservative", "balanced", "aggressive"],
                    "description": "Optional; if omitted, derived from the customer's risk profile",
                },
            },
            "required": ["customer_id", "label", "target_amount", "horizon_years"],
        },
    },
    {
        "name": "simulate_goal",
        "description": "Project the corpus a chosen monthly contribution would reach for a "
        "goal — the 'what-if' lever. Call this when the customer asks what happens if they "
        "invest a different amount.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "label": {"type": "string"},
                "target_amount": {"type": "integer"},
                "horizon_years": {"type": "number"},
                "monthly_contribution": {"type": "integer"},
                "current_savings": {"type": "integer"},
                "bucket": {
                    "type": "string",
                    "enum": ["conservative", "balanced", "aggressive"],
                },
            },
            "required": [
                "customer_id",
                "label",
                "target_amount",
                "horizon_years",
                "monthly_contribution",
            ],
        },
    },
    {
        "name": "search_products",
        "description": "Search the IDBI product catalogue for products matching a need. You "
        "MUST call this to obtain any product before recommending it — never invent a "
        "product, return figure or fee. Returns indicative (not guaranteed) returns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_risk": {"type": "string", "enum": ["low", "medium", "high"]},
                "asset_class": {
                    "type": "string",
                    "enum": ["equity", "debt", "gold", "hybrid", "protection"],
                },
                "category": {"type": "string"},
            },
            "required": ["query"],
        },
    },
]


class ToolExecutor:
    """Executes tool calls for one conversation and records grounded products."""

    def __init__(self, customer_id: str) -> None:
        self._default_customer_id = customer_id
        self._provider = get_provider()
        self._retriever = get_retriever()
        self.grounded_product_ids: Set[str] = set()
        self.grounded_product_names: Set[str] = set()
        self.trace: List[Dict[str, Any]] = []

    # -- helpers ----------------------------------------------------------------

    def _ground(self, product_ids: List[str], product_names: List[str]) -> None:
        self.grounded_product_ids.update(product_ids)
        self.grounded_product_names.update(product_names)

    def _current_monthly_investment(self, customer_id: str) -> float:
        txns = self._provider.get_transactions(customer_id, months=12)
        months = {t.date[:7] for t in txns} or {"_"}
        invested = sum(-t.amount for t in txns if t.category == "investment")
        return invested / len(months)

    def _derive_bucket(self, customer_id: str, horizon_years: float) -> str:
        customer = self._provider.get_customer(customer_id)
        answers = RiskAnswers(
            age=customer.age,
            occupation=customer.occupation,
            dependents=customer.dependents,
            horizon_years=horizon_years,
        )
        return assess_risk(answers).bucket

    # -- dispatch ---------------------------------------------------------------

    def execute(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Run a tool and return a JSON-serialisable result dict."""
        customer_id = payload.get("customer_id", self._default_customer_id)
        try:
            result = self._dispatch(name, customer_id, payload)
            is_error = False
        except KeyError:
            result = {"error": f"Customer {customer_id!r} not found."}
            is_error = True
        except Exception as exc:  # surface tool errors to the model, don't crash the loop
            result = {"error": f"{type(exc).__name__}: {exc}"}
            is_error = True

        self.trace.append({"tool": name, "input": payload, "is_error": is_error})
        return result

    def _dispatch(self, name: str, customer_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if name == "get_customer_profile":
            return self._provider.get_customer(customer_id).model_dump()

        if name == "get_next_best_actions":
            customer = self._provider.get_customer(customer_id)
            txns = self._provider.get_transactions(customer_id, months=18)
            return analyze(customer, txns).model_dump()

        if name == "assess_risk":
            customer = self._provider.get_customer(customer_id)
            answers = RiskAnswers(
                age=customer.age,
                occupation=customer.occupation,
                dependents=customer.dependents,
                horizon_years=payload.get("horizon_years", 7),
                loss_tolerance=payload.get("loss_tolerance", 3),
                has_emergency_fund=payload.get("has_emergency_fund", True),
            )
            return assess_risk(answers).model_dump()

        if name == "plan_goal":
            horizon = float(payload["horizon_years"])
            bucket = payload.get("bucket") or self._derive_bucket(customer_id, horizon)
            goal = Goal(
                label=payload["label"],
                target_amount=int(payload["target_amount"]),
                horizon_years=horizon,
                current_savings=int(payload.get("current_savings", 0)),
            )
            current_sip = self._current_monthly_investment(customer_id)
            plan = plan_goal(goal, bucket, current_monthly_investment=current_sip)
            self._ground(plan.product_ids, [h.product_name for h in plan.allocation.holdings])
            return plan.model_dump()

        if name == "simulate_goal":
            horizon = float(payload["horizon_years"])
            bucket = payload.get("bucket") or self._derive_bucket(customer_id, horizon)
            goal = Goal(
                label=payload["label"],
                target_amount=int(payload["target_amount"]),
                horizon_years=horizon,
                current_savings=int(payload.get("current_savings", 0)),
            )
            return simulate(goal, bucket, float(payload["monthly_contribution"])).model_dump()

        if name == "search_products":
            results = self._retriever.search(
                query=payload["query"],
                max_risk=payload.get("max_risk"),
                asset_class=payload.get("asset_class"),
                category=payload.get("category"),
            )
            products = [p for p, _ in results]
            self._ground([p.product_id for p in products], [p.name for p in products])
            return {
                "products": [
                    {**p.model_dump(), "relevance": score} for p, score in results
                ]
            }

        return {"error": f"Unknown tool: {name}"}
