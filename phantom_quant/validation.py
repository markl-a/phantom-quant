"""Structural validation for chronological OHLCV bar series.

An honest backtest must never run on quietly-wrong data: a bar with high < low,
a zero/negative price, a duplicate or out-of-order timestamp, or a mixed-symbol
series silently corrupts every downstream number. ``validate_bars`` raises a
``BarValidationError`` naming the offending bar rather than letting bad data flow
into the engine.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bars import Bar


class BarValidationError(Exception):
    """Raised when a bar series is structurally invalid for backtesting."""


def _check_price(ts: str, name: str, value: float) -> None:
    """A price must be a finite, strictly-positive number.

    NaN/inf are the dangerous case: ``nan <= 0`` and ``nan < x`` are both False,
    so a non-finite price would slip past every ordering check and silently
    corrupt the backtest. Reject it explicitly here.
    """
    if not math.isfinite(value):
        raise BarValidationError(f"bar {ts}: {name} {value} is not finite")
    if value <= 0:
        raise BarValidationError(f"bar {ts}: {name} {value} must be > 0")


def validate_bars(bars: list[Bar], *, symbol: str | None = None) -> list[Bar]:
    """Validate a chronological bar series and return it unchanged.

    Checks: optional expected-symbol match, single-symbol series, per-bar OHLC
    sanity (high >= low/open/close, low <= open/close, all prices > 0),
    non-negative volume (zero allowed — a halt), and strictly increasing
    timestamps (catching both duplicates and disorder). An empty list is valid.
    """
    if not bars:
        return bars

    series_symbol = bars[0].symbol

    for b in bars:
        if symbol is not None and b.symbol != symbol:
            raise BarValidationError(
                f"bar {b.ts}: symbol {b.symbol!r} != expected {symbol!r}"
            )

        if b.symbol != series_symbol:
            raise BarValidationError(
                f"bar {b.ts}: symbol {b.symbol!r} != series symbol {series_symbol!r}"
            )

        _check_price(b.ts, "open", b.open)
        _check_price(b.ts, "high", b.high)
        _check_price(b.ts, "low", b.low)
        _check_price(b.ts, "close", b.close)

        if b.high < b.low:
            raise BarValidationError(f"bar {b.ts}: high {b.high} < low {b.low}")
        if b.high < b.open:
            raise BarValidationError(f"bar {b.ts}: high {b.high} < open {b.open}")
        if b.high < b.close:
            raise BarValidationError(f"bar {b.ts}: high {b.high} < close {b.close}")
        if b.low > b.open:
            raise BarValidationError(f"bar {b.ts}: low {b.low} > open {b.open}")
        if b.low > b.close:
            raise BarValidationError(f"bar {b.ts}: low {b.low} > close {b.close}")

        if b.volume < 0:
            raise BarValidationError(f"bar {b.ts}: volume {b.volume} < 0")

    for prev, curr in zip(bars, bars[1:]):
        if prev.ts >= curr.ts:
            raise BarValidationError(
                f"non-increasing timestamp: {curr.ts} does not come after {prev.ts}"
            )

    return bars
