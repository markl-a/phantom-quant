"""Configurable, deterministic slippage models.

Slippage models the gap between the price a backtest *decides* to fill at and a
realistic execution: a buy tends to fill a touch higher, a sell a touch lower.
It is applied to the fill price AFTER the no-lookahead gating decision, and is
clamped into the bar's traded range ``[bar.low, bar.high]`` so it can never
invent a price the bar never traded (the same honesty contract the limit-fill
clamp enforces). ``NoSlippage`` is the default and preserves exact-price fills.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


def _validate_side(side: str) -> None:
    if side not in ("buy", "sell"):
        raise ValueError("side must be 'buy' or 'sell'")


def _clamp_to_bar(price: float, bar) -> float:
    return min(max(price, bar.low), bar.high)


class SlippageModel(ABC):
    @abstractmethod
    def adjust(self, side: str, price: float, bar) -> float:
        """Return the adversely-adjusted fill price for `side` ('buy'|'sell'),
        clamped into [bar.low, bar.high]. `bar` is a phantom_quant.bars.Bar."""
        raise NotImplementedError


@dataclass(frozen=True)
class NoSlippage(SlippageModel):
    """Identity model — the default; fills land at exactly the decided price."""

    def adjust(self, side: str, price: float, bar) -> float:
        _validate_side(side)
        return price


@dataclass(frozen=True)
class BpsSlippage(SlippageModel):
    """Adverse slippage of ``bps`` basis points (1 bp = 0.01%)."""

    bps: float = 0.0

    def __post_init__(self) -> None:
        if self.bps < 0:
            raise ValueError("bps must be >= 0")

    def adjust(self, side: str, price: float, bar) -> float:
        _validate_side(side)

        factor = self.bps / 10000.0
        if side == "buy":
            adjusted = price * (1.0 + factor)
        else:
            adjusted = price * (1.0 - factor)

        return _clamp_to_bar(adjusted, bar)
