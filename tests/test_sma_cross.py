from decimal import Decimal

from phantom_quant.bars import Bar
from phantom_quant.strategy import Context, Order
from phantom_quant.strategies.sma_cross import SmaCross


def _ctx(closes, cash="1000000", positions=None):
    hist = [Bar(f"2026-05-{i+1:02d}", "2330", c, c, c, c, 1) for i, c in enumerate(closes)]
    return hist[-1], Context(cash=Decimal(cash), positions=positions or {}, history=hist)


def test_no_order_before_enough_history():
    bar, ctx = _ctx([100, 101, 102])  # < long window
    assert SmaCross(short=2, long=4).on_bar(bar, ctx) == []


def test_buy_when_short_crosses_above_long_and_flat():
    # closes engineered so the short MA crosses above the long MA on the LAST bar
    bar, ctx = _ctx([100, 99, 98, 97, 96, 98, 110])
    orders = SmaCross(short=2, long=4, qty=1000).on_bar(bar, ctx)
    assert orders == [Order("2330", "buy", 1000)]


def test_sell_when_short_crosses_below_long_and_holding():
    bar, ctx = _ctx([100, 101, 102, 103, 104, 102, 90], positions={"2330": 1000})
    orders = SmaCross(short=2, long=4, qty=1000).on_bar(bar, ctx)
    assert orders == [Order("2330", "sell", 1000)]
