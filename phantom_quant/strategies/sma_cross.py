"""SMA crossover — a SKELETON strategy for wiring the pipeline. NOT a profitable
edge; it exists to exercise backtest/paper/live end-to-end.
"""
from __future__ import annotations

from ..bars import Bar
from ..strategy import Context, Order, Strategy


def _sma(values: list[float], n: int) -> float:
    return sum(values[-n:]) / n


class SmaCross(Strategy):
    def __init__(self, short: int = 5, long: int = 20, qty: int = 1000):
        if short >= long:
            raise ValueError("short window must be < long window")
        self.short, self.long, self.qty = short, long, qty

    def on_bar(self, bar: Bar, ctx: Context) -> list[Order]:
        closes = [b.close for b in ctx.history]
        if len(closes) <= self.long:  # need a prior point to detect a cross
            return []
        short_now, long_now = _sma(closes, self.short), _sma(closes, self.long)
        short_prev = _sma(closes[:-1], self.short)
        long_prev = _sma(closes[:-1], self.long)
        held = ctx.positions.get(bar.symbol, 0)
        crossed_up = short_prev <= long_prev and short_now > long_now
        crossed_down = short_prev >= long_prev and short_now < long_now
        if crossed_up and held == 0:
            return [Order(bar.symbol, "buy", self.qty)]
        if crossed_down and held > 0:
            return [Order(bar.symbol, "sell", held)]
        return []
