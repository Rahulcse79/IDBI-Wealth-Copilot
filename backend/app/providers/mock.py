"""Synthetic-data provider for the round-1 (offline) build.

Loads the seeded dataset from ``data/synthetic``. If the dataset is missing (fresh
clone), it is generated on first use so the app runs with zero manual setup.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

from app.models.domain import Customer, Transaction
from app.providers.base import DataProvider


class MockProvider(DataProvider):
    def __init__(self, data_dir: Path, seed: int) -> None:
        self._data_dir = data_dir
        self._seed = seed
        self._customers: Dict[str, Customer] = {}
        self._txns: Dict[str, List[Transaction]] = {}
        self._load()

    # -- loading ----------------------------------------------------------------

    def _load(self) -> None:
        customers_file = self._data_dir / "customers.json"
        txns_file = self._data_dir / "transactions.json"
        if not customers_file.exists() or not txns_file.exists():
            self._bootstrap()

        customers = json.loads(customers_file.read_text())
        txns = json.loads(txns_file.read_text())

        self._customers = {c["customer_id"]: Customer(**c) for c in customers}
        self._txns = {}
        for t in txns:
            self._txns.setdefault(t["customer_id"], []).append(Transaction(**t))
        # Keep each ledger sorted oldest -> newest for deterministic windowing.
        for cid in self._txns:
            self._txns[cid].sort(key=lambda x: x.date)

    def _bootstrap(self) -> None:
        # Imported lazily so the generator isn't a hard import dependency at runtime.
        from data.generate import generate, write

        write(generate(seed=self._seed, n_customers=40, months=18), out_dir=self._data_dir)

    # -- interface --------------------------------------------------------------

    def list_customers(self) -> List[Customer]:
        return list(self._customers.values())

    def get_customer(self, customer_id: str) -> Customer:
        return self._customers[customer_id]

    def get_transactions(self, customer_id: str, months: int = 12) -> List[Transaction]:
        if customer_id not in self._customers:
            raise KeyError(customer_id)
        ledger = self._txns.get(customer_id, [])
        if not ledger:
            return []
        latest = date.fromisoformat(ledger[-1].date)
        cutoff = latest - timedelta(days=int(months * 30.5))
        return [t for t in ledger if date.fromisoformat(t.date) >= cutoff]
