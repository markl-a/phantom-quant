"""Slippage models: adverse fill adjustment, clamped into the bar's traded range.

A buy fills a touch higher and a sell a touch lower, but slippage must never push
the fill beyond [bar.low, bar.high] — a backtest may not invent an un-traded price.
"""
import pytest

from phantom_quant.bars import Bar
from phantom_quant.slippage import BpsSlippage, NoSlippage


def _bar(o=100.0, h=105.0, low=90.0, c=100.0):
    return Bar(ts="t", symbol="X", open=o, high=h, low=low, close=c, volume=1)


def test_no_slippage_returns_price_unchanged_for_buy_and_sell():
    bar = _bar()
    model = NoSlippage()

    assert model.adjust("buy", 100.0, bar) == pytest.approx(100.0)
    assert model.adjust("sell", 100.0, bar) == pytest.approx(100.0)


def test_bps_slippage_buy_applies_adverse_adjustment_within_range():
    bar = _bar(low=90.0, h=105.0)

    assert BpsSlippage(bps=100).adjust("buy", 100.0, bar) == pytest.approx(101.0)


def test_bps_slippage_buy_clamps_to_bar_high():
    bar = _bar(low=90.0, h=100.5)

    assert BpsSlippage(bps=100).adjust("buy", 100.0, bar) == pytest.approx(100.5)


def test_bps_slippage_sell_clamps_to_bar_low():
    bar = _bar(low=99.5, h=105.0)

    assert BpsSlippage(bps=100).adjust("sell", 100.0, bar) == pytest.approx(99.5)


def test_bps_slippage_sell_applies_adverse_adjustment_within_range():
    bar = _bar(o=200.0, low=150.0, h=250.0, c=200.0)

    assert BpsSlippage(bps=50).adjust("sell", 200.0, bar) == pytest.approx(199.0)


def test_bps_slippage_rejects_negative_bps():
    with pytest.raises(ValueError):
        BpsSlippage(bps=-1)


def test_bps_slippage_rejects_unknown_side():
    with pytest.raises(ValueError):
        BpsSlippage(bps=100).adjust("hold", 100.0, _bar())
