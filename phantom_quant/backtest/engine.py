"""Event-driven backtest: feed bars chronologically, call strategy.on_bar,
fill at the bar close, charge the cost model, track the portfolio + equity curve.
Fills-at-close is the simplest honest convention for daily swing bars.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..bars import Bar
from ..portfolio import Portfolio
from ..strategy import Context, Strategy
from .. import costs as _costs
from .execution import FillStatus, decide_fill

__all__ = ["BacktestResult", "run_backtest", "FillStatus"]


@dataclass
class BacktestResult:
    equity_curve: list[tuple[str, Decimal]]
    trades: list[dict]
    portfolio: Portfolio


def run_backtest(bars: list[Bar], strategy: Strategy, cash: Decimal,
                 cost_fn=_costs.trade_cost) -> BacktestResult:
    pf = Portfolio(cash=cash)
    history: list[Bar] = []
    equity_curve: list[tuple[str, Decimal]] = []
    trades: list[dict] = []
    for bar in bars:
        history.append(bar)
        ctx = Context(cash=pf.cash, positions=dict(pf.positions), history=history)
        for order in strategy.on_bar(bar, ctx):
            held = pf.positions.get(order.symbol, 0)
            decision = decide_fill(order, bar, pf.cash, held, cost_fn)
            if decision.status is FillStatus.FILLED:
                price = decision.price
                cost = cost_fn(order.side, price, order.qty)
                pf.apply_fill(order.side, order.symbol, order.qty, price, cost)
            else:
                # gated / rejected orders never touch the portfolio
                price = decision.price
                cost = Decimal("0")
            trades.append({"ts": bar.ts, "symbol": order.symbol, "side": order.side,
                           "qty": order.qty, "price": price, "cost": cost,
                           "status": decision.status, "reason": decision.reason})
        equity_curve.append((bar.ts, pf.equity({bar.symbol: bar.close})))
    return BacktestResult(equity_curve=equity_curve, trades=trades, portfolio=pf)
