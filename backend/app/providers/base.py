"""Provider interface.

Everything above this seam (quant engine, agent, API) depends only on this
abstract interface — never on where the data comes from. Round 1 uses
:class:`~app.providers.mock.MockProvider` (synthetic data); after IDBI shortlisting
unlocks the sandbox, a ``SandboxProvider`` implements the same methods against the
bank's APIs and is selected via ``WEALTH_DATA_PROVIDER=sandbox``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.models.domain import Customer, Transaction


class DataProvider(ABC):
    """Read access to customer financial data."""

    @abstractmethod
    def list_customers(self) -> List[Customer]:
        """Return all customers (demo/admin use)."""

    @abstractmethod
    def get_customer(self, customer_id: str) -> Customer:
        """Return one customer or raise ``KeyError``."""

    @abstractmethod
    def get_transactions(self, customer_id: str, months: int = 12) -> List[Transaction]:
        """Return the customer's transactions over the trailing ``months`` window."""
