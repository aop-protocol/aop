"""Budgets and budget alerts.

A budget is a (cap, period, scope) policy. As cost events stream in, the
runtime accumulates spend per scope; threshold breaches fire user-supplied
alert callbacks. Persistence is deliberately out of scope here — wire a
storage backend in if you want durable budgets.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional


class BudgetExceeded(RuntimeError):
    """Raised by Budget.check() when ``raise_on_exceed`` is True."""


@dataclass
class BudgetAlert:
    threshold_pct: float                   # e.g. 0.5, 0.8, 1.0
    callback: Callable[["Budget", float], None]
    fired: bool = False                    # set True after first fire


@dataclass
class Budget:
    name: str
    cap_amount: float
    currency: str = "USD"
    period: str = "month"                   # "day" | "week" | "month" | "lifetime"
    scope: Dict[str, Any] = field(default_factory=dict)
    alerts: List[BudgetAlert] = field(default_factory=list)
    raise_on_exceed: bool = False

    _spent: float = field(default=0.0, init=False, repr=False)
    _period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc),
                                    init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    # ------------------------------------------------------------------
    def add_alert(self, threshold_pct: float, callback: Callable[["Budget", float], None]) -> None:
        self.alerts.append(BudgetAlert(threshold_pct=threshold_pct, callback=callback))

    def reset(self) -> None:
        with self._lock:
            self._spent = 0.0
            self._period_start = datetime.now(timezone.utc)
            for a in self.alerts:
                a.fired = False

    @property
    def spent(self) -> float:
        return self._spent

    @property
    def remaining(self) -> float:
        return max(0.0, self.cap_amount - self._spent)

    # ------------------------------------------------------------------
    def matches(self, event: Dict[str, Any]) -> bool:
        if not self.scope:
            return True
        for k, v in self.scope.items():
            if event.get(k) != v:
                # Try data.* lookups
                data = event.get("data") or {}
                if data.get(k) != v:
                    return False
        return True

    def observe(self, event: Dict[str, Any]) -> bool:
        """Account for an event. Returns True if any alert fired in this call."""
        cost = event.get("cost") or {}
        amount = cost.get("amount")
        if amount is None or not self.matches(event):
            return False
        currency = cost.get("currency", self.currency)
        if currency != self.currency:
            return False
        self._roll_period_if_due()

        fired_this_call = False
        with self._lock:
            self._spent += float(amount)
            for alert in self.alerts:
                if alert.fired:
                    continue
                if self._spent >= self.cap_amount * alert.threshold_pct:
                    alert.fired = True
                    fired_this_call = True
                    try:
                        alert.callback(self, self._spent)
                    except Exception:
                        pass
        if self.raise_on_exceed and self._spent > self.cap_amount:
            raise BudgetExceeded(
                f"budget {self.name!r} exceeded: {self._spent:.4f} > {self.cap_amount:.4f}"
            )
        return fired_this_call

    # ------------------------------------------------------------------
    def _roll_period_if_due(self) -> None:
        if self.period == "lifetime":
            return
        now = datetime.now(timezone.utc)
        delta = {
            "day": timedelta(days=1),
            "week": timedelta(weeks=1),
            "month": timedelta(days=30),
        }.get(self.period)
        if delta is None:
            return
        if now - self._period_start >= delta:
            self.reset()
