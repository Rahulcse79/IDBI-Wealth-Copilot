"""Portfolio construction.

Maps a risk bucket to a strategic asset allocation and grounds each asset class in a
real catalogue product. Returns the blended expected return used by goal planning.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel

from app.quant.constants import ALLOCATIONS, ASSET_CLASS_PRODUCT, ASSET_RETURN
from data.catalogue import get_product


class Holding(BaseModel):
    asset_class: str
    weight: float  # 0..1
    product_id: str
    product_name: str
    indicative_return_pa: float


class Portfolio(BaseModel):
    bucket: str
    holdings: List[Holding]
    blended_return_pa: float
    product_ids: List[str]  # grounded products the copilot is allowed to cite


def build_portfolio(bucket: str) -> Portfolio:
    """Build a model portfolio for a risk bucket."""
    if bucket not in ALLOCATIONS:
        raise ValueError(f"Unknown risk bucket: {bucket!r}")

    holdings: List[Holding] = []
    blended = 0.0
    for asset_class, weight in ALLOCATIONS[bucket].items():
        product = get_product(ASSET_CLASS_PRODUCT[asset_class])
        holdings.append(
            Holding(
                asset_class=asset_class,
                weight=round(weight, 4),
                product_id=product.product_id,
                product_name=product.name,
                indicative_return_pa=product.indicative_return_pa,
            )
        )
        blended += weight * ASSET_RETURN[asset_class]

    return Portfolio(
        bucket=bucket,
        holdings=holdings,
        blended_return_pa=round(blended, 4),
        product_ids=[h.product_id for h in holdings],
    )
