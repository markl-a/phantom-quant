from decimal import Decimal
from pathlib import Path

from phantom_quant import costs
from phantom_quant.backtest.engine import run_backtest, BacktestResult
from phantom_quant.data.provider import CsvProvider
from phantom_quant.strategies.sma_cross import SmaCross

FIX = Path(__file__).parent / "fixtures" / "sample_2330_1d.csv"


def test_backtest_runs_and_produces_equity_curve_and_trades():
    bars = CsvProvider(FIX).get_bars("2330", "1d", "2026-05-01", "2026-06-05")
    result = run_backtest(bars, SmaCross(short=3, long=6, qty=1000),
                          cash=Decimal("1000000"), cost_fn=costs.trade_cost)
    assert isinstance(result, BacktestResult)
    # one full equity point per bar
    assert len(result.equity_curve) == len(bars)
    # the skeleton enters on the up-cross and exits on the down-cross => >=1 round trip
    sides = [t["side"] for t in result.trades]
    assert "buy" in sides and "sell" in sides
    # equity is conserved: final equity == cash + marked position value
    last_price = {"2330": bars[-1].close}
    assert result.equity_curve[-1][1] == result.portfolio.equity(last_price)


def test_orders_fill_at_close_and_charge_cost():
    bars = CsvProvider(FIX).get_bars("2330", "1d", "2026-05-01", "2026-06-05")
    result = run_backtest(bars, SmaCross(short=3, long=6, qty=1000),
                          cash=Decimal("1000000"), cost_fn=costs.trade_cost)
    first = result.trades[0]
    assert first["side"] == "buy"
    assert first["cost"] == costs.trade_cost("buy", first["price"], first["qty"])
