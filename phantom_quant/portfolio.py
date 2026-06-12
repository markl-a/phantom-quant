"""Portfolio accounting. Money is Decimal end-to-end (sibling to phantom-finance).

Realized PnL uses average-cost basis. Cost (fee/tax) is added to the buy basis
and subtracted from sell proceeds, so realized PnL is already net of costs.
"""
from __future__ import annotations

from decimal import Decimal


class Portfolio:
    def __init__(self, cash: Decimal):
        self.cash: Decimal = Decimal(cash)
        self.positions: dict[str, int] = {}
        self.realized: Decimal = Decimal("0")
        self._basis: dict[str, Decimal] = {}  # symbol -> total net cost of open shares

    def apply_fill(self, side: str, symbol: str, qty: int, price: float, cost: Decimal) -> None:
        notional = Decimal(str(price)) * Decimal(qty)
        held = self.positions.get(symbol, 0)
        if side == "buy":
            self.cash -= notional + cost
            self.positions[symbol] = held + qty
            self._basis[symbol] = self._basis.get(symbol, Decimal("0")) + notional + cost
        elif side == "sell":
            if qty > held:
                raise ValueError(f"cannot sell {qty} of {symbol}; only hold {held}")
            self.cash += notional - cost
            avg = self._basis.get(symbol, Decimal("0")) / Decimal(held) if held else Decimal("0")
            basis_sold = avg * Decimal(qty)
            self.realized += (notional - cost) - basis_sold
            self.positions[symbol] = held - qty
            self._basis[symbol] = self._basis.get(symbol, Decimal("0")) - basis_sold
            if self.positions[symbol] == 0:
                self.positions.pop(symbol, None)
                self._basis.pop(symbol, None)
        else:
            raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")

    def market_value(self, prices: dict[str, float]) -> Decimal:
        total = Decimal("0")
        for sym, qty in self.positions.items():
            total += Decimal(str(prices[sym])) * Decimal(qty)
        return total

    def equity(self, prices: dict[str, float]) -> Decimal:
        return self.cash + self.market_value(prices)
