"""The agent loop.

Runs a manual Claude tool-calling loop (full control over logging + guardrails), then
validates the final answer and, if a compliance check fails, gives the model exactly one
chance to correct itself before falling back to a safe message.

Uses ``claude-opus-4-8`` with adaptive thinking (per the project's Claude API guidance).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.agent.guardrails import SAFE_FALLBACK, ValidationResult, validate_response
from app.agent.prompts import SYSTEM_PROMPT, customer_context
from app.agent.tools import TOOLS, ToolExecutor
from app.config import anthropic_key_available, get_settings

_MAX_TOOL_ITERATIONS = 8


class CopilotConfigError(RuntimeError):
    """Raised when the copilot cannot run (e.g. no Anthropic credential configured)."""


class CopilotReply(BaseModel):
    answer: str
    tool_trace: List[Dict[str, Any]]
    grounded_products: List[str]
    guardrail_triggered: bool
    guardrail_violations: List[Dict[str, Any]]


def _text_of(content: List[Any]) -> str:
    return "\n".join(b.text for b in content if getattr(b, "type", None) == "text").strip()


def _client():
    import anthropic  # imported lazily so the rest of the app runs without the SDK

    return anthropic.Anthropic()


class Copilot:
    """Stateless-per-call orchestrator. Conversation history is passed in by the caller."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def run(
        self,
        customer_id: str,
        customer_name: str,
        history: List[Dict[str, str]],
        user_message: str,
    ) -> CopilotReply:
        if not anthropic_key_available():
            raise CopilotConfigError(
                "No Anthropic credential found. Set ANTHROPIC_API_KEY (or run `ant auth login`) "
                "to enable the conversational copilot. The quant endpoints work without it."
            )

        client = _client()
        executor = ToolExecutor(customer_id)
        system = f"{SYSTEM_PROMPT}\n\n{customer_context(customer_id, customer_name)}"

        messages: List[Dict[str, Any]] = [
            {"role": m["role"], "content": m["content"]} for m in history
        ]
        messages.append({"role": "user", "content": user_message})

        try:
            response = self._run_tool_loop(client, system, messages, executor)
        except Exception as exc:  # noqa: BLE001 — map SDK/API errors to a friendly message
            raise self._map_api_error(exc)
        answer = _text_of(response.content)

        result = validate_response(answer, executor.grounded_product_names)
        if result.blocking:
            answer, result = self._correct(client, system, messages, executor, result)

        return CopilotReply(
            answer=answer or SAFE_FALLBACK,
            tool_trace=executor.trace,
            grounded_products=sorted(executor.grounded_product_names),
            guardrail_triggered=result.blocking,
            guardrail_violations=[v.model_dump() for v in result.violations],
        )

    # -- internals --------------------------------------------------------------

    @staticmethod
    def _map_api_error(exc: Exception) -> Exception:
        """Translate Anthropic SDK/API errors into a user-facing CopilotConfigError."""
        import anthropic

        if isinstance(exc, anthropic.AuthenticationError):
            return CopilotConfigError("The Anthropic API key is invalid or has been revoked.")
        if isinstance(exc, anthropic.APIStatusError):
            msg = str(getattr(exc, "message", exc)).lower()
            if "credit balance" in msg or "billing" in msg:
                return CopilotConfigError(
                    "The Anthropic account for this key has no API credits. Add credits in "
                    "Plans & Billing to enable the copilot — the quick-action demos still work."
                )
            if isinstance(exc, anthropic.RateLimitError):
                return CopilotConfigError("The copilot is rate-limited right now; please retry shortly.")
            return CopilotConfigError(f"The copilot is temporarily unavailable ({exc}).")
        if isinstance(exc, anthropic.APIError):
            return CopilotConfigError(f"The copilot could not reach the Anthropic API ({exc}).")
        return exc

    def _create(self, client, system: str, messages: List[Dict[str, Any]]):
        base = dict(
            model=self._settings.model,
            max_tokens=self._settings.max_tokens,
            system=system,
            messages=messages,
            tools=TOOLS,
        )
        # Prefer adaptive thinking + effort (per the project's Claude API guidance), but
        # fall back gracefully if the installed SDK / API version doesn't accept them.
        attempts = [
            dict(base, thinking={"type": "adaptive"}, output_config={"effort": self._settings.effort}),
            dict(base, thinking={"type": "adaptive"}),
            base,
        ]
        last_exc: Exception = RuntimeError("no attempt made")
        for kwargs in attempts:
            try:
                return client.messages.create(**kwargs)
            except TypeError as exc:  # SDK doesn't know a kwarg
                last_exc = exc
                continue
            except Exception as exc:  # noqa: BLE001 — retry only param-shape errors
                msg = str(exc).lower()
                if any(p in msg for p in ("thinking", "effort", "output_config")):
                    last_exc = exc
                    continue
                raise
        raise last_exc

    def _run_tool_loop(self, client, system, messages, executor: ToolExecutor):
        response = self._create(client, system, messages)
        for _ in range(_MAX_TOOL_ITERATIONS):
            messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason != "tool_use":
                break

            tool_results = []
            for block in response.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                result = executor.execute(block.name, dict(block.input))
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                        "is_error": "error" in result,
                    }
                )
            messages.append({"role": "user", "content": tool_results})
            response = self._create(client, system, messages)
        return response

    def _correct(
        self,
        client,
        system: str,
        messages: List[Dict[str, Any]],
        executor: ToolExecutor,
        result: ValidationResult,
    ):
        """Give the model one corrective turn to fix a compliance violation."""
        issues = "; ".join(v.message for v in result.violations)
        messages.append(
            {
                "role": "user",
                "content": (
                    f"[Compliance check failed: {issues}] Rewrite your previous answer. Do not "
                    "promise guaranteed, assured, or risk-free returns, and only mention products "
                    "you have looked up via search_products in this conversation (call it now if "
                    "needed). Keep the rest of your guidance."
                ),
            }
        )
        response = self._run_tool_loop(client, system, messages, executor)
        answer = _text_of(response.content)
        recheck = validate_response(answer, executor.grounded_product_names)
        if recheck.blocking:
            return SAFE_FALLBACK, recheck
        return answer, recheck
