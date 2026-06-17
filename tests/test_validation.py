"""Bar-series structural validation: bad data must fail loud, not flow silently.

A backtest may not run on a series with high < low, zero/negative prices,
negative volume, duplicate/out-of-order timestamps, or mixed symbols.
"""
import pytest

from phantom_quant.bars import Bar
from phantom_quant.validation import BarValidationError, validate_bars


def test_clean_three_bar_series_validates_and_returns_unchanged_identity():
    bars = [
        Bar(ts="2024-01-01", symbol="2330", open=100, high=110, low=95, close=105, volume=1000),
        Bar(ts="2024-01-02", symbol="2330", open=105, high=112, low=101, close=108, volume=1200),
        Bar(ts="2024-01-03", symbol="2330", open=108, high=115, low=106, close=111, volume=900),
    ]

    assert validate_bars(bars) is bars


def test_empty_list_returns_empty_list():
    assert validate_bars([]) == []


def test_high_less_than_low_raises_with_timestamp():
    bars = [
        Bar(ts="2024-01-01", symbol="2330", open=100, high=99, low=101, close=100, volume=1000),
    ]

    with pytest.raises(BarValidationError) as exc:
        validate_bars(bars)

    assert "2024-01-01" in str(exc.value)


def test_zero_price_raises():
    bars = [
        Bar(ts="2024-01-01", symbol="2330", open=0, high=110, low=95, close=105, volume=1000),
    ]

    with pytest.raises(BarValidationError):
        validate_bars(bars)


def test_negative_price_raises():
    bars = [
        Bar(ts="2024-01-01", symbol="2330", open=100, high=110, low=95, close=-1, volume=1000),
    ]

    with pytest.raises(BarValidationError):
        validate_bars(bars)


def test_negative_volume_raises_and_zero_volume_is_allowed():
    negative_volume_bars = [
        Bar(ts="2024-01-01", symbol="2330", open=100, high=110, low=95, close=105, volume=-1),
    ]

    with pytest.raises(BarValidationError):
        validate_bars(negative_volume_bars)

    zero_volume_bars = [
        Bar(ts="2024-01-01", symbol="2330", open=100, high=110, low=95, close=105, volume=0),
    ]

    assert validate_bars(zero_volume_bars) is zero_volume_bars


def test_nan_price_raises():
    # NaN slips past every ordering comparison (nan <= 0 is False, nan < x is
    # False), so it must be rejected explicitly or it corrupts the backtest.
    bars = [
        Bar(ts="2024-01-01", symbol="2330", open=float("nan"), high=110, low=95,
            close=105, volume=1000),
    ]
    with pytest.raises(BarValidationError) as exc:
        validate_bars(bars)
    assert "finite" in str(exc.value)


def test_inf_price_raises():
    bars = [
        Bar(ts="2024-01-01", symbol="2330", open=100, high=float("inf"), low=95,
            close=105, volume=1000),
    ]
    with pytest.raises(BarValidationError) as exc:
        validate_bars(bars)
    assert "finite" in str(exc.value)


def test_high_less_than_open_raises():
    bars = [
        Bar(ts="2024-01-01", symbol="2330", open=100, high=99, low=95, close=98, volume=1000),
    ]

    with pytest.raises(BarValidationError):
        validate_bars(bars)


def test_low_greater_than_close_raises():
    bars = [
        Bar(ts="2024-01-01", symbol="2330", open=105, high=110, low=101, close=100, volume=1000),
    ]

    with pytest.raises(BarValidationError):
        validate_bars(bars)


def test_duplicate_timestamp_raises():
    bars = [
        Bar(ts="2024-01-01", symbol="2330", open=100, high=110, low=95, close=105, volume=1000),
        Bar(ts="2024-01-01", symbol="2330", open=105, high=112, low=101, close=108, volume=1200),
    ]

    with pytest.raises(BarValidationError):
        validate_bars(bars)


def test_out_of_order_timestamp_raises():
    bars = [
        Bar(ts="2024-01-02", symbol="2330", open=105, high=112, low=101, close=108, volume=1200),
        Bar(ts="2024-01-01", symbol="2330", open=100, high=110, low=95, close=105, volume=1000),
    ]

    with pytest.raises(BarValidationError):
        validate_bars(bars)


def test_symbol_argument_mismatch_raises():
    bars = [
        Bar(ts="2024-01-01", symbol="2330", open=100, high=110, low=95, close=105, volume=1000),
    ]

    with pytest.raises(BarValidationError):
        validate_bars(bars, symbol="2317")


def test_mixed_symbols_without_symbol_argument_raises():
    bars = [
        Bar(ts="2024-01-01", symbol="2330", open=100, high=110, low=95, close=105, volume=1000),
        Bar(ts="2024-01-02", symbol="2317", open=105, high=112, low=101, close=108, volume=1200),
    ]

    with pytest.raises(BarValidationError):
        validate_bars(bars)
