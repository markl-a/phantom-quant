from decimal import Decimal

from phantom_quant.backtest.engine import BacktestResult
from phantom_quant.portfolio import Portfolio
from phantom_quant import report


def _result():
    curve = [("2026-05-01", Decimal("1000000")),
             ("2026-05-02", Decimal("1010000")),
             ("2026-05-03", Decimal("990000")),
             ("2026-05-04", Decimal("1030000"))]
    trades = [{"ts": "2026-05-02", "symbol": "2330", "side": "buy", "qty": 1000,
               "price": 100.0, "cost": Decimal("142")},
              {"ts": "2026-05-04", "symbol": "2330", "side": "sell", "qty": 1000,
               "price": 103.0, "cost": Decimal("451")}]
    return BacktestResult(curve, trades, Portfolio(Decimal("1030000")))


def test_metrics_are_data_derived():
    m = report.metrics(_result())
    assert m["total_return"] == Decimal("0.03")  # 1030000/1000000 - 1
    assert m["max_drawdown"] == Decimal("0.0198")  # (990000-1010000)/1010000 rounded
    assert m["num_trades"] == 2


def test_markdown_contains_headline_numbers():
    md = report.to_markdown(_result(), {"symbol": "2330", "strategy": "sma_cross"})
    assert "# phantom-quant backtest" in md
    assert "2330" in md and "sma_cross" in md
    assert "3.00%" in md  # total return rendered
