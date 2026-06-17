"""Request/response models for the HTTP API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CustomerSummary(BaseModel):
    customer_id: str
    name: str
    age: int
    city: str
    occupation: str


class RiskRequest(BaseModel):
    customer_id: str
    horizon_years: float = 7
    loss_tolerance: int = Field(default=3, ge=1, le=5)
    has_emergency_fund: bool = True


class GoalRequest(BaseModel):
    customer_id: str
    label: str
    target_amount: int
    horizon_years: float
    current_savings: int = 0
    bucket: Optional[str] = None


class SimulateRequest(BaseModel):
    customer_id: str
    label: str = "goal"
    target_amount: int
    horizon_years: float
    monthly_contribution: int
    current_savings: int = 0
    bucket: Optional[str] = None


class ChatTurn(BaseModel):
    role: str  # user | assistant
    content: str


class ChatRequest(BaseModel):
    customer_id: str
    message: str
    history: List[ChatTurn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    tool_trace: List[Dict[str, Any]]
    grounded_products: List[str]
    guardrail_triggered: bool
    guardrail_violations: List[Dict[str, Any]]


class ConfigResponse(BaseModel):
    copilot_available: bool
    model: str
    data_provider: str
