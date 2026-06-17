"""Hermetic simulated paper trading over the BarEventDriver stream.

This module is intentionally narrow: it provides a live-looking paper-trading
core that runs entirely in memory and produces the same result shape as the
backtest engine.

``PaperAccount`` is a thin state holder around ``Portfolio``. It owns the
portfolio, equity curve, trade tape, and last-price marks used for equity
calculation. It does not persist state to disk.

``PaperBroker`` is a ``BarEvent`` consumer. On each bar it mirrors the
``run_backtest`` per-bar body and delegates all trading math to the same
primitives: ``decide_fill``, ``Portfolio.apply_fill``, ``slippage.adjust``, the
configured ``cost_fn``, and ``limit_lock.lock_blocks``. Paper trading therefore
does not reimplement fill rules, accounting, slippage, costs, or limit-lock
behavior.

``run_paper`` wires a ``BarEventDriver`` to a ``PaperBroker`` and returns
``BacktestResult(equity_curve, trades, portfolio)`` so callers can compare
paper output directly with ``run_backtest``.

HONEST-BAIL: this is not a live broker. A real Shioaji/live adapter, persistent
disk state, and real-time pacing are the next item and are deliberately not
implemented here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from . import costs as _costs
from . import limit_lock as _limit_lock
from .backtest.engine import BacktestResult
from .backtest.execution import FillDecision, FillStatus, decide_fill
from .bars import Bar
from .driver import BarConsumer, BarEvent, BarEventDriver
from .portfolio import Portfolio
from .slippage import NoSlippage, SlippageModel
from .strategy import Context, Strategy

__all__ = ["PaperAccount", "Broker", "PaperBroker", "run_paper"]


class PaperAccount:
    """Live simulated account: Portfolio + equity curve + trades + marks."""

    def __init__(self, cash: Decimal):
        self.portfolio = Portfolio(cash)
        self.equity_curve: list[tuple[str, Decimal]] = []
        self.trades: list[dict] = []
        self.last_price: dict[str, float] = {}

    @property
    def cash(self) -> Decimal:
        return self.portfolio.cash

    @property
    def positions(self) -> dict[str, int]:
        return self.portfolio.positions

    @property
    def realized_pnl(self) -> Decimal:
        return self.portfolio.realized

    def equity(self) -> Decimal:
        return self.portfolio.equity(self.last_price)


class Broker(ABC):
    """Broker interface for future live adapters.

    HONEST-BAIL: real Shioaji/live brokerage integration, persistent disk state,
    and real-time pacing are the next item; they are not implemented here.
    """

    @abstractmethod
    def on_bar(self, event: BarEvent) -> None:
        raise NotImplementedError


class PaperBroker(Broker):
    """In-memory broker that consumes ``BarEvent`` objects like a BarConsumer."""

    def __init__(
        self,
        strategy: Strategy,
        account: PaperAccount,
        *,
        cost_fn=_costs.trade_cost,
        slippage: SlippageModel = NoSlippage(),
    ) -> None:
        self.strategy = strategy
        self.account = account
        self.cost_fn = cost_fn
        self.slippage = slippage
        self._history: list[Bar] = []

    def on_bar(self, event: BarEvent) -> None:
        bar = event.bar
        pf = self.account.portfolio
        last_price = self.account.last_price
        history = self._history
        trades = self.account.trades
        equity_curve = self.account.equity_curve
        cost_fn = self.cost_fn
        slippage = self.slippage
        strategy = self.strategy

        prev_close = last_price.get(bar.symbol)
        history.append(bar)
        last_price[bar.symbol] = bar.close
        ctx = Context(cash=pf.cash, positions=dict(pf.positions), history=history)
        for order in strategy.on_bar(bar, ctx):
            held = pf.positions.get(order.symbol, 0)
            if order.symbol != bar.symbol:
                decision = FillDecision(
                    FillStatus.GATED,
                    None,
                    f"order symbol {order.symbol!r} != bar symbol {bar.symbol!r}",
                )
            else:
                decision = decide_fill(order, bar, pf.cash, held, cost_fn)
                if decision.status is FillStatus.FILLED:
                    lock_reason = _limit_lock.lock_blocks(order.side, bar, prev_close)
                    if lock_reason is not None:
                        decision = FillDecision(FillStatus.GATED, None, lock_reason)
            if decision.status is FillStatus.FILLED:
                price = slippage.adjust(order.side, decision.price, bar)
                cost = cost_fn(order.side, price, order.qty)
                if order.side == "buy":
                    notional = Decimal(str(price)) * Decimal(order.qty)
                    if notional + cost > pf.cash:
                        decision = FillDecision(
                            FillStatus.GATED,
                            None,
                            f"insufficient cash after slippage: need "
                            f"{notional + cost}, have {pf.cash}",
                        )
                        price, cost = None, Decimal("0")
                if decision.status is FillStatus.FILLED:
                    pf.apply_fill(order.side, order.symbol, order.qty, price, cost)
            else:
                price = decision.price
                cost = Decimal("0")
            trades.append(
                {
                    "ts": bar.ts,
                    "symbol": order.symbol,
                    "side": order.side,
                    "qty": order.qty,
                    "price": price,
                    "cost": cost,
                    "status": decision.status,
                    "reason": decision.reason,
                }
            )
        equity_curve.append((bar.ts, pf.equity(last_price)))


def run_paper(
    bars: list[Bar],
    strategy: Strategy,
    cash: Decimal,
    *,
    cost_fn=_costs.trade_cost,
    slippage: SlippageModel = NoSlippage(),
) -> BacktestResult:
    """Run bars through ``BarEventDriver`` and return the backtest result shape.

    The returned ``BacktestResult`` has the same fields as ``run_backtest`` so
    simulated paper runs can be compared directly to backtest runs.
    """
    account = PaperAccount(cash)
    broker = PaperBroker(strategy, account, cost_fn=cost_fn, slippage=slippage)
    driver = BarEventDriver(bars)
    consumer: BarConsumer = broker
    driver.register(consumer)
    driver.run()
    return BacktestResult(
        equity_curve=account.equity_curve,
        trades=account.trades,
        portfolio=account.portfolio,
    )
