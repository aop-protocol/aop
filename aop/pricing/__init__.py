"""LLM pricing book + cost calculator.

The pricing book is a versioned JSON document under ``aop/pricing/data/``
keyed by ``(provider, model)``. ``compute_cost(...)`` returns a fully
populated AOP ``cost`` field that can be attached to any LLM event.

Numbers are best-effort and updated periodically; users can override or add
entries via :func:`register_price`.
"""

from .price_book import (
    PriceEntry,
    compute_cost,
    estimate_cost_usd,
    register_price,
    get_price,
    all_prices,
    reload_prices,
)
from .budget import Budget, BudgetAlert, BudgetExceeded

__all__ = [
    "PriceEntry",
    "compute_cost",
    "estimate_cost_usd",
    "register_price",
    "get_price",
    "all_prices",
    "reload_prices",
    "Budget",
    "BudgetAlert",
    "BudgetExceeded",
]
