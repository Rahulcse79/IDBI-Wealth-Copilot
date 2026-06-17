"""Compliance guardrails — enforced in code, unit-tested independently of the LLM.

Two checks run over the copilot's final text:

1. No guaranteed/assured returns — a bank must never let an advisor promise returns.
2. Product grounding — any *catalogue* product named in the answer must have been
   looked up via ``search_products`` / ``plan_goal`` this turn (tracked by the
   :class:`~app.agent.tools.ToolExecutor`). This catches a real product cited without
   grounding. (It cannot catch a fully invented product name; the system prompt plus
   the "you must call search_products" instruction handle that case.)
"""

from __future__ import annotations

import re
from typing import List, Set

from pydantic import BaseModel

from data.catalogue import valid_product_names

# A "guarantee" word, a negation, and a returns context. We flag an *affirmative*
# guarantee of returns, but NOT compliant phrasing like "returns are not guaranteed".
_GUARANTEE_WORD = re.compile(r"\b(guarantee[ds]?|assured|risk[-\s]?free)\b", re.IGNORECASE)
_NEGATION = re.compile(
    r"\b(not|never|no|cannot|can\s?not|without|neither|nothing|isn't|aren't|won't|"
    r"don't|doesn't|can't)\b|n't\b",
    re.IGNORECASE,
)
_RETURN_CONTEXT = re.compile(
    r"\b(returns?|profit|\d+(\.\d+)?\s?%|p\.?\s?a\.?)\b", re.IGNORECASE
)


def _is_affirmative_return_guarantee(text: str, match: "re.Match") -> bool:
    """True if a guarantee word is (a) not negated and (b) in a returns context."""
    before = text[max(0, match.start() - 30) : match.start()]
    if _NEGATION.search(before):
        return False
    around = text[max(0, match.start() - 40) : match.end() + 45]
    return bool(_RETURN_CONTEXT.search(around))


class Violation(BaseModel):
    type: str  # guaranteed_return | ungrounded_product
    message: str
    snippet: str


class ValidationResult(BaseModel):
    ok: bool
    violations: List[Violation]

    @property
    def blocking(self) -> bool:
        return not self.ok


def check_guaranteed_returns(text: str) -> List[Violation]:
    violations: List[Violation] = []
    for match in _GUARANTEE_WORD.finditer(text):
        if _is_affirmative_return_guarantee(text, match):
            snippet = text[max(0, match.start() - 20) : match.end() + 25].strip()
            violations.append(
                Violation(
                    type="guaranteed_return",
                    message="Response appears to promise a guaranteed or assured return.",
                    snippet=snippet,
                )
            )
            break  # one is enough to block
    return violations


def check_products_grounded(text: str, allowed_names: Set[str]) -> List[Violation]:
    violations: List[Violation] = []
    lowered = text.lower()
    for name in valid_product_names():
        if name.lower() in lowered and name not in allowed_names:
            violations.append(
                Violation(
                    type="ungrounded_product",
                    message=f"Cited catalogue product '{name}' that was not looked up this turn.",
                    snippet=name,
                )
            )
    return violations


def validate_response(text: str, grounded_names: Set[str]) -> ValidationResult:
    """Run all guardrail checks over the copilot's final answer."""
    violations = check_guaranteed_returns(text) + check_products_grounded(text, grounded_names)
    return ValidationResult(ok=not violations, violations=violations)


# A safe, compliant message used when the model cannot be corrected within the loop.
SAFE_FALLBACK = (
    "I can't promise guaranteed returns — all market-linked investments carry risk. "
    "I can, however, walk you through suitable IDBI options with their indicative "
    "(not guaranteed) returns and the risks involved. Would you like me to do that?"
)
