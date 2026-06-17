"""Event-driven backtest: feed bars chronologically, call strategy.on_bar,
fill at the bar close, charge the cost model, track the portfolio + equity curve.
Fills-at-close is the simplest honest convention for daily swing bars.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..bars import Bar
from ..portfolio import Portfolio
from ..slippage import NoSlippage, SlippageModel
from ..strategy import Context, Strategy
from .. import costs as _costs
from .execution import FillDecision, FillStatus, decide_fill

__all__ = ["BacktestResult", "run_backtest", "FillStatus"]


@dataclass
class BacktestResult:
    equity_curve: list[tuple[str, Decimal]]
    trades: list[dict]
    portfolio: Portfolio


def run_backtest(bars: list[Bar], strategy: Strategy, cash: Decimal,
                 cost_fn=_costs.trade_cost,
                 slippage: SlippageModel = NoSlippage()) -> BacktestResult:
    pf = Portfolio(cash=cash)
    history: list[Bar] = []
    equity_curve: list[tuple[str, Decimal]] = []
    trades: list[dict] = []
    # Mark equity from the last-known close of EVERY symbol the portfolio has
    # seen, not just the current bar's symbol — otherwise marking a portfolio
    # that holds another symbol would KeyError. Single-symbol runs are unchanged.
    last_price: dict[str, float] = {}
    for bar in bars:
        history.append(bar)
        last_price[bar.symbol] = bar.close
        ctx = Context(cash=pf.cash, positions=dict(pf.positions), history=history)
        for order in strategy.on_bar(bar, ctx):
            held = pf.positions.get(order.symbol, 0)
            if order.symbol != bar.symbol:
                # An order can only fill against a bar of the SAME symbol; the
                # current bar carries no price for any other symbol. Gate it.
                decision = FillDecision(
                    FillStatus.GATED, None,
                    f"order symbol {order.symbol!r} != bar symbol {bar.symbol!r}")
            else:
                decision = decide_fill(order, bar, pf.cash, held, cost_fn)
            if decision.status is FillStatus.FILLED:
                # Apply slippage to the decided price, then (for a buy) re-check
                # affordability: slippage can only RAISE a buy price, so a fill
                # that was affordable at the decided price may no longer be.
                price = slippage.adjust(order.side, decision.price, bar)
                cost = cost_fn(order.side, price, order.qty)
                if order.side == "buy":
                    notional = Decimal(str(price)) * Decimal(order.qty)
                    if notional + cost > pf.cash:
                        decision = FillDecision(
                            FillStatus.GATED, None,
                            f"insufficient cash after slippage: need "
                            f"{notional + cost}, have {pf.cash}")
                        price, cost = None, Decimal("0")
                if decision.status is FillStatus.FILLED:
                    pf.apply_fill(order.side, order.symbol, order.qty, price, cost)
            else:
                # gated / rejected orders never touch the portfolio
                price = decision.price
                cost = Decimal("0")
            trades.append({"ts": bar.ts, "symbol": order.symbol, "side": order.side,
                           "qty": order.qty, "price": price, "cost": cost,
                           "status": decision.status, "reason": decision.reason})
        equity_curve.append((bar.ts, pf.equity(last_price)))
    return BacktestResult(equity_curve=equity_curve, trades=trades, portfolio=pf)
