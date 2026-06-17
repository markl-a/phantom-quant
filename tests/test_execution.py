"""P1-1 — backtest execution realism: order-status validation + fill gating.

Orders must only fill under realistic conditions. An order that cannot
realistically fill on the given bar is *gated* (recorded with a non-filled
status), never silently filled. Every number is derived from a deterministic
fixture price series so the assertions are independently re-computable.
"""
from decimal import Decimal

import pytest

from phantom_quant.bars import Bar
from phantom_quant.backtest.engine import run_backtest, FillStatus
from phantom_quant.strategy import Context, Order, Strategy
from phantom_quant import costs


# --- deterministic fixtures -------------------------------------------------

def _bars(rows):
    """rows: list of (ts, open, high, low, close, volume)."""
    return [Bar(ts, "2330", o, h, l, c, v) for (ts, o, h, l, c, v) in rows]


class _ScriptedStrategy(Strategy):
    """Emits a pre-scripted order on a given bar timestamp (no logic)."""

    def __init__(self, orders_by_ts):
        self._orders_by_ts = orders_by_ts

    def on_bar(self, bar, ctx):
        return list(self._orders_by_ts.get(bar.ts, []))


PRICES = _bars([
    ("2026-05-01", 100.0, 102.0, 99.0, 101.0, 10000),
    ("2026-05-02", 101.0, 105.0, 100.0, 104.0, 12000),
    ("2026-05-03", 104.0, 106.0, 103.0, 105.0, 0),       # zero-volume / halted bar
    ("2026-05-04", 105.0, 108.0, 104.0, 107.0, 15000),
])


# --- valid market order fills at close with correct status ------------------

def test_valid_market_order_fills_with_status_filled():
    strat = _ScriptedStrategy({"2026-05-01": [Order("2330", "buy", 1000)]})
    res = run_backtest(PRICES, strat, cash=Decimal("1000000"), cost_fn=costs.trade_cost)
    fills = [t for t in res.trades if t["ts"] == "2026-05-01"]
    assert len(fills) == 1
    t = fills[0]
    assert t["status"] == FillStatus.FILLED
    # market order fills at the bar close (deterministic: 101.0)
    assert t["price"] == 101.0
    assert res.portfolio.positions.get("2330") == 1000


# --- a limit buy below the bar's low cannot realistically fill --------------

def test_unfillable_limit_buy_is_gated_not_filled():
    # buy limit at 95 on a bar whose low is 99 -> price never reached -> gated
    strat = _ScriptedStrategy({
        "2026-05-01": [Order("2330", "buy", 1000, type="limit", limit_price=95.0)]
    })
    res = run_backtest(PRICES, strat, cash=Decimal("1000000"), cost_fn=costs.trade_cost)
    t = [x for x in res.trades if x["ts"] == "2026-05-01"][0]
    assert t["status"] == FillStatus.GATED
    # no position taken, no cash spent
    assert res.portfolio.positions.get("2330", 0) == 0
    assert res.portfolio.cash == Decimal("1000000")


def test_marketable_limit_buy_fills_at_limit_price():
    # buy limit at 101 on a bar whose low is 99 -> reachable -> fills at the limit
    strat = _ScriptedStrategy({
        "2026-05-01": [Order("2330", "buy", 1000, type="limit", limit_price=101.0)]
    })
    res = run_backtest(PRICES, strat, cash=Decimal("1000000"), cost_fn=costs.trade_cost)
    t = [x for x in res.trades if x["ts"] == "2026-05-01"][0]
    assert t["status"] == FillStatus.FILLED
    assert t["price"] == 101.0


# --- a halted / zero-volume bar cannot fill ---------------------------------

def test_zero_volume_bar_gates_the_fill():
    strat = _ScriptedStrategy({"2026-05-03": [Order("2330", "buy", 1000)]})
    res = run_backtest(PRICES, strat, cash=Decimal("1000000"), cost_fn=costs.trade_cost)
    t = [x for x in res.trades if x["ts"] == "2026-05-03"][0]
    assert t["status"] == FillStatus.GATED
    assert res.portfolio.positions.get("2330", 0) == 0


# --- structurally invalid orders are rejected (validation), not filled ------

def test_invalid_qty_is_rejected():
    strat = _ScriptedStrategy({"2026-05-01": [Order("2330", "buy", 0)]})
    res = run_backtest(PRICES, strat, cash=Decimal("1000000"), cost_fn=costs.trade_cost)
    t = [x for x in res.trades if x["ts"] == "2026-05-01"][0]
    assert t["status"] == FillStatus.REJECTED
    assert res.portfolio.cash == Decimal("1000000")


def test_invalid_side_is_rejected():
    strat = _ScriptedStrategy({"2026-05-01": [Order("2330", "hold", 1000)]})
    res = run_backtest(PRICES, strat, cash=Decimal("1000000"), cost_fn=costs.trade_cost)
    t = [x for x in res.trades if x["ts"] == "2026-05-01"][0]
    assert t["status"] == FillStatus.REJECTED


def test_limit_order_without_limit_price_is_rejected():
    strat = _ScriptedStrategy({
        "2026-05-01": [Order("2330", "buy", 1000, type="limit", limit_price=None)]
    })
    res = run_backtest(PRICES, strat, cash=Decimal("1000000"), cost_fn=costs.trade_cost)
    t = [x for x in res.trades if x["ts"] == "2026-05-01"][0]
    assert t["status"] == FillStatus.REJECTED


# --- a buy the portfolio cannot afford is gated (no negative cash) ----------

def test_unaffordable_buy_is_gated():
    # only 1000 cash; one share of ~101 costs >100k notional -> cannot afford
    strat = _ScriptedStrategy({"2026-05-01": [Order("2330", "buy", 1000)]})
    res = run_backtest(PRICES, strat, cash=Decimal("1000"), cost_fn=costs.trade_cost)
    t = [x for x in res.trades if x["ts"] == "2026-05-01"][0]
    assert t["status"] == FillStatus.GATED
    assert res.portfolio.cash == Decimal("1000")  # untouched


# --- selling more than held is gated (no negative position) -----------------

def test_oversell_is_gated():
    strat = _ScriptedStrategy({"2026-05-01": [Order("2330", "sell", 1000)]})
    res = run_backtest(PRICES, strat, cash=Decimal("1000000"), cost_fn=costs.trade_cost)
    t = [x for x in res.trades if x["ts"] == "2026-05-01"][0]
    assert t["status"] == FillStatus.GATED
    assert res.portfolio.positions.get("2330", 0) == 0


# --- only filled orders mutate the portfolio; equity stays consistent -------

def test_only_filled_orders_change_equity():
    # one gated order (limit too low) then a real market buy next bar
    strat = _ScriptedStrategy({
        "2026-05-01": [Order("2330", "buy", 1000, type="limit", limit_price=10.0)],
        "2026-05-02": [Order("2330", "buy", 1000)],
    })
    res = run_backtest(PRICES, strat, cash=Decimal("1000000"), cost_fn=costs.trade_cost)
    statuses = {t["ts"]: t["status"] for t in res.trades}
    assert statuses["2026-05-01"] == FillStatus.GATED
    assert statuses["2026-05-02"] == FillStatus.FILLED
    # equity curve last point still equals portfolio equity marked at last close
    last_close = PRICES[-1].close
    assert res.equity_curve[-1][1] == res.portfolio.equity({"2330": last_close})
