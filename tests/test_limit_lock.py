"""台股 ±10% limit-lock (漲跌停) gating.

A buy can't fill on a locked limit-up bar (no sellers); a sell can't fill on a
locked limit-down bar (no buyers). A bar that only touches a limit intraday is
not locked.
"""
import pytest

from phantom_quant.bars import Bar
from phantom_quant.limit_lock import (
    limit_band, is_locked_up, is_locked_down, lock_blocks,
)


def _bar(o, h, low, c):
    return Bar(ts="t", symbol="X", open=o, high=h, low=low, close=c, volume=1)


def test_limit_band_is_plus_minus_10_percent():
    floor, ceiling = limit_band(100.0)
    assert floor == pytest.approx(90.0)
    assert ceiling == pytest.approx(110.0)


def test_limit_band_rejects_nonpositive_prev_close():
    with pytest.raises(ValueError):
        limit_band(0.0)


def test_locked_up_bar_is_detected():
    # prev close 100 -> ceiling 110; bar pinned at 110 (low==high==110) is locked up
    bar = _bar(110.0, 110.0, 110.0, 110.0)
    assert is_locked_up(bar, 100.0)
    assert not is_locked_down(bar, 100.0)


def test_locked_down_bar_is_detected():
    # prev close 100 -> floor 90; bar pinned at 90 is locked down
    bar = _bar(90.0, 90.0, 90.0, 90.0)
    assert is_locked_down(bar, 100.0)
    assert not is_locked_up(bar, 100.0)


def test_bar_touching_ceiling_only_at_high_is_not_locked():
    # high reaches the ceiling but the bar traded lower -> not locked
    bar = _bar(105.0, 110.0, 104.0, 109.0)
    assert not is_locked_up(bar, 100.0)


def test_buy_blocked_on_locked_up_bar():
    bar = _bar(110.0, 110.0, 110.0, 110.0)
    assert lock_blocks("buy", bar, 100.0) is not None
    assert "limit-up" in lock_blocks("buy", bar, 100.0)
    # a sell is fine on a locked-up bar (there ARE buyers at the ceiling)
    assert lock_blocks("sell", bar, 100.0) is None


def test_sell_blocked_on_locked_down_bar():
    bar = _bar(90.0, 90.0, 90.0, 90.0)
    assert lock_blocks("sell", bar, 100.0) is not None
    assert "limit-down" in lock_blocks("sell", bar, 100.0)
    assert lock_blocks("buy", bar, 100.0) is None


def test_no_prior_close_does_not_block():
    bar = _bar(110.0, 110.0, 110.0, 110.0)
    assert lock_blocks("buy", bar, None) is None


def test_invalid_side_raises():
    bar = _bar(100.0, 101.0, 99.0, 100.0)
    with pytest.raises(ValueError):
        lock_blocks("hold", bar, 100.0)
