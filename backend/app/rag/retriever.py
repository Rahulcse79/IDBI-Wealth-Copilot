"""Lightweight TF-IDF product retriever.

Pure Python (no heavy ML dependency) so it runs offline and deterministically. Indexes
the product catalogue once and ranks products against a free-text query by cosine
similarity, with optional structured filters. This is the grounding step: only products
returned here may be recommended to the customer.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from app.models.domain import Product
from data.catalogue import all_products

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


def _doc_text(p: Product) -> str:
    return " ".join(
        [p.name, p.category, p.asset_class, p.risk_level, p.description, p.lock_in]
    )


class ProductRetriever:
    """In-memory TF-IDF index over the product catalogue."""

    def __init__(self, products: List[Product]) -> None:
        self._products = products
        self._tf: List[Counter] = [Counter(_tokenize(_doc_text(p))) for p in products]
        self._idf: Dict[str, float] = self._compute_idf()
        self._vectors: List[Dict[str, float]] = [self._tfidf(tf) for tf in self._tf]
        self._norms: List[float] = [self._norm(v) for v in self._vectors]

    def _compute_idf(self) -> Dict[str, float]:
        n_docs = len(self._products)
        df: Counter = Counter()
        for tf in self._tf:
            df.update(tf.keys())
        return {term: math.log((1 + n_docs) / (1 + freq)) + 1.0 for term, freq in df.items()}

    def _tfidf(self, tf: Counter) -> Dict[str, float]:
        total = sum(tf.values()) or 1
        return {term: (count / total) * self._idf.get(term, 0.0) for term, count in tf.items()}

    @staticmethod
    def _norm(vec: Dict[str, float]) -> float:
        return math.sqrt(sum(w * w for w in vec.values())) or 1.0

    def _passes_filters(
        self,
        p: Product,
        category: Optional[str],
        asset_class: Optional[str],
        max_risk: Optional[str],
    ) -> bool:
        if category and p.category != category:
            return False
        if asset_class and p.asset_class != asset_class:
            return False
        if max_risk:
            order = {"low": 0, "medium": 1, "high": 2}
            if order.get(p.risk_level, 1) > order.get(max_risk, 2):
                return False
        return True

    def search(
        self,
        query: str,
        top_k: int = 4,
        category: Optional[str] = None,
        asset_class: Optional[str] = None,
        max_risk: Optional[str] = None,
    ) -> List[Tuple[Product, float]]:
        """Return up to ``top_k`` (product, score) pairs ranked by relevance."""
        q_tf = Counter(_tokenize(query))
        q_vec = self._tfidf(q_tf)
        q_norm = self._norm(q_vec)

        scored: List[Tuple[Product, float]] = []
        for idx, product in enumerate(self._products):
            if not self._passes_filters(product, category, asset_class, max_risk):
                continue
            dot = sum(w * self._vectors[idx].get(term, 0.0) for term, w in q_vec.items())
            score = dot / (q_norm * self._norms[idx])
            scored.append((product, round(score, 4)))

        scored.sort(key=lambda pair: pair[1], reverse=True)
        # If the query was empty/irrelevant, still return filtered products by min investment.
        if not query.strip():
            scored.sort(key=lambda pair: pair[0].min_investment)
        return scored[:top_k]


@lru_cache
def get_retriever() -> ProductRetriever:
    """Process-wide cached retriever built from the catalogue."""
    return ProductRetriever(all_products())
