"""Structural validation for chronological OHLCV bar series."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bars import Bar


class BarValidationError(Exception):
    """Raised when a bar series is structurally invalid for backtesting."""


def validate_bars(bars: list[Bar], *, symbol: str | None = None) -> list[Bar]:
    """Validate a chronological bar series and return it unchanged."""
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

        if b.open <= 0:
            raise BarValidationError(f"bar {b.ts}: open {b.open} must be > 0")
        if b.high <= 0:
            raise BarValidationError(f"bar {b.ts}: high {b.high} must be > 0")
        if b.low <= 0:
            raise BarValidationError(f"bar {b.ts}: low {b.low} must be > 0")
        if b.close <= 0:
            raise BarValidationError(f"bar {b.ts}: close {b.close} must be > 0")

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
