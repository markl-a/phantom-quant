"""OHLCV bar — the atomic unit fed through the backtest engine."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bar:
    ts: str  # ISO date or datetime string
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
