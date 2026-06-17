"""台股 daily ±10% limit-lock (漲跌停) helpers for honest offline backtests.

Taiwan stocks may only move ±10% from the prior session's close in a day. When a
stock is *locked* limit-up the whole day trades pinned at the ceiling with no
sellers, so a BUY cannot realistically fill; locked limit-down pins at the floor
with no buyers, so a SELL cannot fill. The backtest must not pretend it filled.
This models the *locked* (fully-pinned) case only, conservatively — a bar that
merely touches a limit intraday is not treated as locked.
"""
from __future__ import annotations

import math


LIMIT_PCT = 0.10
_EPSILON = 1e-9


def limit_band(prev_close: float) -> tuple[float, float]:
    """Return the raw +/-10% price band from the prior session close."""
    if prev_close <= 0:
        raise ValueError("prev_close must be positive")

    return (
        prev_close * (1.0 - LIMIT_PCT),
        prev_close * (1.0 + LIMIT_PCT),
    )


def is_locked_up(bar, prev_close: float) -> bool:
    """Return True when the whole traded range is pinned at limit-up."""
    _, ceiling = limit_band(prev_close)
    return bar.low >= ceiling - _EPSILON or math.isclose(
        bar.low,
        ceiling,
        abs_tol=_EPSILON,
    )


def is_locked_down(bar, prev_close: float) -> bool:
    """Return True when the whole traded range is pinned at limit-down."""
    floor, _ = limit_band(prev_close)
    return bar.high <= floor + _EPSILON


def lock_blocks(side: str, bar, prev_close: float) -> str | None:
    """Return a reason when a side is blocked by a locked limit bar."""
    if side not in ("buy", "sell"):
        raise ValueError("side must be 'buy' or 'sell'")

    if prev_close is None:
        return None

    if side == "buy" and is_locked_up(bar, prev_close):
        return "buy blocked: locked limit-up, no sellers"

    if side == "sell" and is_locked_down(bar, prev_close):
        return "sell blocked: locked limit-down, no buyers"

    return None
