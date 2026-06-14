"""The strategy contract — the interface a strategy implements.

A strategy reacts to one bar at a time via on_bar. Today this runs only in the
backtest engine. The contract is deliberately execution-agnostic so the same
on_bar code could later drive paper/live trading, but that wiring is not built
yet (paper/live are roadmap).
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
