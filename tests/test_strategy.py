from decimal import Decimal

import pytest

from phantom_quant.bars import Bar
from phantom_quant.strategy import Strategy, Order, Context


def test_order_is_frozen_with_defaults():
    o = Order(symbol="2330", side="buy", qty=1000)
    assert o.type == "market" and o.limit_price is None


def test_strategy_is_abstract():
    with pytest.raises(TypeError):
        Strategy()  # type: ignore[abstract]


def test_concrete_strategy_receives_bar_and_context():
    class Buy1(Strategy):
        def on_bar(self, bar, ctx):
            return [Order(bar.symbol, "buy", 1000)]

    bar = Bar("2026-06-01", "2330", 900, 910, 895, 905, 1)
    ctx = Context(cash=Decimal("1000000"), positions={}, history=[bar])
    orders = Buy1().on_bar(bar, ctx)
    assert orders == [Order("2330", "buy", 1000)]
