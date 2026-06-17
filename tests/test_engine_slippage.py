"""Engine-level integration of slippage + multi-symbol equity marking.

Slippage is applied to the FILLED price inside run_backtest (after gating),
clamped to the bar; a buy made unaffordable by slippage is gated. Equity is
marked from the last-known close of every symbol seen, not just the current bar's.
"""
from decimal import Decimal

from phantom_quant.bars import Bar
from phantom_quant.backtest.engine import run_backtest, FillStatus
from phantom_quant.slippage import BpsSlippage
from phantom_quant.strategy import Order, Strategy
from phantom_quant import costs


def _bars(symbol, rows):
    return [Bar(ts, symbol, o, h, l, c, v) for (ts, o, h, l, c, v) in rows]


class _Scripted(Strategy):
    def __init__(self, orders_by_ts):
        self._orders_by_ts = orders_by_ts

    def on_bar(self, bar, ctx):
        return list(self._orders_by_ts.get(bar.ts, []))


PRICES = _bars("2330", [
    ("2026-05-01", 100.0, 110.0, 90.0, 100.0, 10000),
    ("2026-05-02", 100.0, 110.0, 90.0, 105.0, 12000),
])


def test_buy_slippage_raises_fill_price_through_engine():
    strat = _Scripted({"2026-05-01": [Order("2330", "buy", 1000)]})
    res = run_backtest(PRICES, strat, cash=Decimal("1000000"),
                       cost_fn=costs.trade_cost, slippage=BpsSlippage(bps=100))
    t = [x for x in res.trades if x["ts"] == "2026-05-01"][0]
    assert t["status"] == FillStatus.FILLED
    # close 100 * (1 + 0.01) = 101.0, within [90, 110]
    assert t["price"] == 101.0


def test_sell_slippage_lowers_fill_price_through_engine():
    strat = _Scripted({
        "2026-05-01": [Order("2330", "buy", 1000)],
        "2026-05-02": [Order("2330", "sell", 1000)],
    })
    res = run_backtest(PRICES, strat, cash=Decimal("1000000"),
                       cost_fn=costs.trade_cost, slippage=BpsSlippage(bps=100))
    sell = [x for x in res.trades if x["ts"] == "2026-05-02"][0]
    assert sell["status"] == FillStatus.FILLED
    # close 105 * (1 - 0.01) = 103.95, within [90, 110]
    assert abs(sell["price"] - 103.95) < 1e-9


def test_buy_made_unaffordable_by_slippage_is_gated():
    # Exactly enough cash for a fill at 100 close but not after +1% slippage.
    # notional at 100 = 100000; fee floor 20 -> need 100020 cash.
    # at 101 notional = 101000 -> unaffordable.
    strat = _Scripted({"2026-05-01": [Order("2330", "buy", 1000)]})
    res = run_backtest(PRICES, strat, cash=Decimal("100500"),
                       cost_fn=costs.trade_cost, slippage=BpsSlippage(bps=100))
    t = [x for x in res.trades if x["ts"] == "2026-05-01"][0]
    assert t["status"] == FillStatus.GATED
    assert "after slippage" in t["reason"]
    assert res.portfolio.cash == Decimal("100500")  # untouched


class _PerSymbolBuyOnce(Strategy):
    """Buy 1000 of each symbol the first time its own bar is seen."""

    def __init__(self):
        self._bought: set[str] = set()

    def on_bar(self, bar, ctx):
        if bar.symbol in self._bought:
            return []
        self._bought.add(bar.symbol)
        return [Order(bar.symbol, "buy", 1000)]


def test_multi_symbol_equity_marks_all_held_symbols():
    # Two interleaved symbols; each order fills against ITS OWN symbol's bar.
    # Marking equity must not KeyError and must price BOTH holdings at their
    # last-known close.
    bars = [
        Bar("2026-05-01", "AAA", 50.0, 55.0, 45.0, 50.0, 10000),
        Bar("2026-05-01", "BBB", 20.0, 22.0, 18.0, 20.0, 10000),
        Bar("2026-05-02", "AAA", 50.0, 60.0, 48.0, 55.0, 10000),
        Bar("2026-05-02", "BBB", 20.0, 25.0, 19.0, 24.0, 10000),
    ]
    res = run_backtest(bars, _PerSymbolBuyOnce(), cash=Decimal("1000000"),
                       cost_fn=costs.trade_cost)
    # final equity = cash + 1000*55 (AAA last close) + 1000*24 (BBB last close)
    expected = res.portfolio.cash + Decimal("55") * 1000 + Decimal("24") * 1000
    assert res.equity_curve[-1][1] == expected
    assert res.portfolio.positions == {"AAA": 1000, "BBB": 1000}


def test_order_for_other_symbol_is_gated():
    bars = [Bar("2026-05-01", "AAA", 50.0, 55.0, 45.0, 50.0, 10000)]
    strat = _Scripted({"2026-05-01": [Order("BBB", "buy", 1000)]})
    res = run_backtest(bars, strat, cash=Decimal("1000000"), cost_fn=costs.trade_cost)
    t = res.trades[0]
    assert t["status"] == FillStatus.GATED
    assert "!= bar symbol" in t["reason"]
    assert res.portfolio.positions == {}
