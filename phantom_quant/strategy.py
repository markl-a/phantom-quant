"""The strategy contract — the stable interface across backtest / paper / live.

A strategy reacts to one bar at a time. The SAME on_bar code runs in the
backtest engine (P0), paper trading (P1), and live (P2) — that is the whole
point of event-driven over vectorized.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal

from .bars import Bar


@dataclass(frozen=True)
class Order:
    symbol: str
    side: str  # "buy" | "sell"
    qty: int
    type: str = "market"
    limit_price: float | None = None


@dataclass
class Context:
    cash: Decimal
    positions: dict[str, int] = field(default_factory=dict)
    history: list[Bar] = field(default_factory=list)  # bars up to & including current


class Strategy(ABC):
    @abstractmethod
    def on_bar(self, bar: Bar, ctx: Context) -> list[Order]:
        """Return zero or more orders to submit after seeing `bar`."""
        raise NotImplementedError
