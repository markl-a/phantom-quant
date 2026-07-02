from __future__ import annotations

from decimal import Decimal

import pytest

from phantom_quant.backtest.engine import BacktestResult
from phantom_quant.bars import Bar
from phantom_quant.portfolio import Portfolio
from phantom_quant.risk import exposure_and_turnover


def _backtest_result(
    equity_curve: list[tuple[str, str]], trades: list[dict]
) -> BacktestResult:
    return BacktestResult(
        equity_curve=[(ts, Decimal(v)) for ts, v in equity_curve],
        trades=trades,
        portfolio=Portfolio(cash=Decimal("100000")),
    )


class TestExposureAndTurnover:
    def test_hand_computed_values(self):
        bars = [
            Bar(ts="2026-01-01", symbol="AAPL", open=150, high=155, low=149, close=152, volume=10000),
            Bar(ts="2026-01-02", symbol="AAPL", open=152, high=153, low=148, close=149, volume=10000),
        ]
        trades = [
            {"status": "filled", "ts": "2026-01-01", "price": 150, "qty": 100, "side": "buy", "symbol": "AAPL"},
        ]
        result = _backtest_result(
            equity_curve=[("2026-01-01", "100000"), ("2026-01-02", "101500")],
            trades=trades,
        )
        out = exposure_and_turnover(result, bars)

        turnover_notional = Decimal("150") * Decimal("100")
        start_equity = Decimal("100000")
        expected_turnover = turnover_notional / start_equity
        assert out["turnover"] == str(expected_turnover.quantize(Decimal("0.0001")))

        assert out["average_exposure"] == "0.1494"
        assert out["max_exposure"] == "0.1520"

    def test_non_filled_trades_are_excluded(self):
        bars = [
            Bar(ts="2026-01-01", symbol="AAPL", open=150, close=152, high=155, low=149, volume=10000),
        ]
        trades = [
            {"status": "cancelled", "ts": "2026-01-01", "price": 150, "qty": 100, "side": "buy", "symbol": "AAPL"},
        ]
        result = _backtest_result(
            equity_curve=[("2026-01-01", "100000")],
            trades=trades,
        )
        out = exposure_and_turnover(result, bars)
        assert out["turnover"] == "0.0000", "cancelled trade must not contribute to turnover"
        assert out["average_exposure"] == "0.0000", "cancelled trade must not add exposure"

    def test_price_none_trades_excluded_from_turnover(self):
        bars = [
            Bar(ts="2026-01-01", symbol="AAPL", open=150, close=152, high=155, low=149, volume=10000),
        ]
        trades = [
            {"status": "filled", "ts": "2026-01-01", "price": None, "qty": 100, "side": "buy", "symbol": "AAPL"},
        ]
        result = _backtest_result(
            equity_curve=[("2026-01-01", "100000")],
            trades=trades,
        )
        out = exposure_and_turnover(result, bars)
        assert out["turnover"] == "0.0000", "price=None trade must not contribute to turnover"
