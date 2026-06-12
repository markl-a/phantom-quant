"""台股 現股 transaction cost model — a first-class citizen of every backtest.

Honest backtests MUST charge real costs or the numbers lie.
- 手續費 (fee): 0.1425% of notional, floored to NT$1, min NT$20 per side.
- 證交稅 (tax): 0.3% of notional, sell side only, floored to NT$1.
- discount: broker fee discount multiplier (e.g. Decimal("0.6") for 6 折).
"""
from __future__ import annotations

from decimal import Decimal, ROUND_FLOOR

FEE_RATE = Decimal("0.001425")
TAX_RATE = Decimal("0.003")
MIN_FEE = Decimal("20")
LOT_SIZE = 1000  # 1 張 = 1000 股


def tick_size(price: float) -> Decimal:
    p = Decimal(str(price))
    if p < 10:
        return Decimal("0.01")
    if p < 50:
        return Decimal("0.05")
    if p < 100:
        return Decimal("0.1")
    if p < 500:
        return Decimal("0.5")
    if p < 1000:
        return Decimal("1")
    return Decimal("5")


def _notional(price: float, qty: int) -> Decimal:
    return Decimal(str(price)) * Decimal(qty)


def fee(price: float, qty: int, discount: Decimal = Decimal("1")) -> Decimal:
    raw = (_notional(price, qty) * FEE_RATE * discount).quantize(Decimal("1"), ROUND_FLOOR)
    return max(raw, MIN_FEE)


def tax(price: float, qty: int) -> Decimal:
    return (_notional(price, qty) * TAX_RATE).quantize(Decimal("1"), ROUND_FLOOR)


def trade_cost(side: str, price: float, qty: int, discount: Decimal = Decimal("1")) -> Decimal:
    if side not in ("buy", "sell"):
        raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")
    total = fee(price, qty, discount)
    if side == "sell":
        total += tax(price, qty)
    return total
