"""Application settings.

Settings are read from environment variables (prefixed ``WEALTH_``) or a local
``.env`` file. Secrets (the Anthropic key) are intentionally *not* surfaced here —
the Anthropic SDK resolves ``ANTHROPIC_API_KEY`` / an ``ant`` profile on its own.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _load_local_env() -> None:
    """Load ``backend/.env`` into ``os.environ`` so the Anthropic SDK (which reads the
    process environment, not a ``.env`` file) picks up ``ANTHROPIC_API_KEY``.

    Only sets keys that aren't already present, so a real shell export always wins.
    """
    env_path = _BACKEND_ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_local_env()


class Settings(BaseSettings):
    """Runtime configuration with safe defaults for the round-1 (offline) build."""

    model_config = SettingsConfigDict(env_prefix="WEALTH_", env_file=".env", extra="ignore")

    # LLM
    model: str = "claude-opus-4-8"
    effort: str = "medium"  # low | medium | high | max — depth/cost of the agent loop
    max_tokens: int = 4096

    # Data
    data_provider: str = "mock"  # mock (synthetic) now, sandbox (IDBI API) after shortlisting
    data_dir: Path = _BACKEND_ROOT / "data" / "synthetic"
    seed: int = 20260617

    # Quant assumptions surfaced for transparency (see quant/constants.py for the rest)
    emergency_fund_months: int = 6


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached :class:`Settings` instance."""
    return Settings()


def anthropic_key_available() -> bool:
    """True if a credential the Anthropic SDK can use appears to be configured."""
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
