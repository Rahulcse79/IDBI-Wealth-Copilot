"""Provider selection based on settings (the env-var swap seam)."""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.providers.base import DataProvider


@lru_cache
def get_provider() -> DataProvider:
    """Return the configured data provider (cached for the process lifetime)."""
    settings = get_settings()
    if settings.data_provider == "mock":
        from app.providers.mock import MockProvider

        return MockProvider(data_dir=settings.data_dir, seed=settings.seed)

    # Placeholder for the post-shortlisting integration:
    # if settings.data_provider == "sandbox":
    #     from app.providers.sandbox import SandboxProvider
    #     return SandboxProvider(...)

    raise ValueError(f"Unknown data_provider: {settings.data_provider!r}")
