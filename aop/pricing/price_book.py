"""LLM price book.

Prices are stored as USD-per-1M-tokens. The price book is loaded from
``aop/pricing/data/price_book.json`` at import time. Users can override
entries with :func:`register_price` or replace the file via env var
``AOP_PRICING_FILE``.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional, Tuple

_log = logging.getLogger("aop.pricing")


@dataclass(frozen=True)
class PriceEntry:
    provider: str
    model: str
    input_per_million: float       # USD per million input tokens
    output_per_million: float      # USD per million output tokens
    cached_input_per_million: Optional[float] = None
    currency: str = "USD"
    effective_date: Optional[str] = None
    source: Optional[str] = None


_lock = RLock()
_book: Dict[Tuple[str, str], PriceEntry] = {}


def _data_path() -> Path:
    override = os.environ.get("AOP_PRICING_FILE")
    if override:
        return Path(override)
    return Path(__file__).parent / "data" / "price_book.json"


def reload_prices() -> int:
    """Reload the price book from disk. Returns the number of entries loaded."""
    path = _data_path()
    if not path.exists():
        return 0
    try:
        with open(path) as f:
            payload = json.load(f)
    except Exception as e:
        _log.warning("failed to load price book %s: %s", path, e)
        return 0

    with _lock:
        _book.clear()
        for row in payload.get("prices", []):
            try:
                entry = PriceEntry(**row)
                _book[(entry.provider.lower(), entry.model.lower())] = entry
            except Exception as e:
                _log.debug("skipping invalid price row %r: %s", row, e)
    return len(_book)


def register_price(entry: PriceEntry) -> None:
    """Add or replace a price-book entry at runtime."""
    with _lock:
        _book[(entry.provider.lower(), entry.model.lower())] = entry


def get_price(provider: str, model: str) -> Optional[PriceEntry]:
    if not provider or not model:
        return None
    p, m = provider.lower(), model.lower()
    with _lock:
        if (p, m) in _book:
            return _book[(p, m)]
        # try prefix matches: "gpt-4o-mini-2024-07-18" -> "gpt-4o-mini"
        for (prov, mdl), entry in _book.items():
            if prov == p and m.startswith(mdl):
                return entry
    return None


def all_prices() -> Dict[Tuple[str, str], PriceEntry]:
    with _lock:
        return dict(_book)


# ---------------------------------------------------------------------------
# Cost calculation
# ---------------------------------------------------------------------------

def estimate_cost_usd(
    provider: str, model: str,
    prompt_tokens: int, completion_tokens: int,
    *, cached_input_tokens: int = 0,
) -> Optional[float]:
    entry = get_price(provider, model)
    if entry is None:
        return None
    in_rate = entry.input_per_million / 1_000_000
    out_rate = entry.output_per_million / 1_000_000
    paid_input = max(0, prompt_tokens - cached_input_tokens)
    cost = paid_input * in_rate + completion_tokens * out_rate
    if cached_input_tokens and entry.cached_input_per_million is not None:
        cost += cached_input_tokens * (entry.cached_input_per_million / 1_000_000)
    return round(cost, 8)


def compute_cost(
    *,
    provider: str, model: str,
    prompt_tokens: int, completion_tokens: int,
    cached_input_tokens: int = 0,
) -> Optional[Dict[str, Any]]:
    """Return a fully-populated ``cost`` dict suitable for an AOP event."""
    entry = get_price(provider, model)
    if entry is None:
        return None
    amount = estimate_cost_usd(provider, model, prompt_tokens, completion_tokens,
                               cached_input_tokens=cached_input_tokens)
    if amount is None:
        return None
    return {
        "amount": amount,
        "currency": entry.currency,
        "model": entry.model,
        "provider": entry.provider,
        "cost_per_input_token": entry.input_per_million / 1_000_000,
        "cost_per_output_token": entry.output_per_million / 1_000_000,
    }


# Eagerly load on import so users can call compute_cost() right away.
reload_prices()
