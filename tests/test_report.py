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
    assert "realized PnL" in md  # richer line surfaced


def test_richer_metrics_keys_present_and_typed():
    m = report.metrics(_result())
    # existing keys preserved (back-compat)
    for k in ("start_equity", "end_equity", "total_return", "max_drawdown",
              "num_trades", "num_closed"):
        assert k in m
    # new keys
    for k in ("ending_cash", "realized_pnl", "total_costs",
              "num_gated", "num_rejected", "wins", "losses"):
        assert k in m
    assert isinstance(m["total_costs"], Decimal)
    assert isinstance(m["ending_cash"], Decimal)
    assert isinstance(m["realized_pnl"], Decimal)
    assert isinstance(m["wins"], int) and isinstance(m["losses"], int)
    # the _result() tape: buy 100 -> sell 103, one profitable closed round-trip
    assert m["wins"] == 1 and m["losses"] == 0
    # costs paid = 142 (buy) + 451 (sell)
    assert m["total_costs"] == Decimal("593")
    assert m["num_gated"] == 0 and m["num_rejected"] == 0


def test_win_loss_counts_a_losing_round_trip():
    curve = [("d1", Decimal("1000000")), ("d2", Decimal("990000"))]
    trades = [
        {"ts": "d1", "symbol": "2330", "side": "buy", "qty": 1000,
         "price": 100.0, "cost": Decimal("142"), "status": "filled"},
        {"ts": "d2", "symbol": "2330", "side": "sell", "qty": 1000,
         "price": 95.0, "cost": Decimal("420"), "status": "filled"},
    ]
    m = report.metrics(BacktestResult(curve, trades, Portfolio(Decimal("990000"))))
    assert m["wins"] == 0 and m["losses"] == 1


def test_win_loss_is_quantity_aware_for_multi_lot_sells():
    # buy 2000@100, then two 1000-share sells at 90 (loss) and 110 (win):
    # quantity-aware FIFO must count one loss and one win, not collapse to one.
    curve = [("d1", Decimal("1")), ("d4", Decimal("1"))]
    trades = [
        {"ts": "d1", "symbol": "2330", "side": "buy", "qty": 2000,
         "price": 100.0, "cost": Decimal("0"), "status": "filled"},
        {"ts": "d2", "symbol": "2330", "side": "sell", "qty": 1000,
         "price": 90.0, "cost": Decimal("0"), "status": "filled"},
        {"ts": "d3", "symbol": "2330", "side": "sell", "qty": 1000,
         "price": 110.0, "cost": Decimal("0"), "status": "filled"},
    ]
    m = report.metrics(BacktestResult(curve, trades, Portfolio(Decimal("1"))))
    assert m["wins"] == 1 and m["losses"] == 1


def test_win_loss_splits_one_sell_across_two_buy_lots():
    # buy 1000@100, buy 1000@200, sell 2000@150 -> chunk vs 100 = win, vs 200 = loss
    curve = [("d1", Decimal("1")), ("d3", Decimal("1"))]
    trades = [
        {"ts": "d1", "symbol": "2330", "side": "buy", "qty": 1000,
         "price": 100.0, "cost": Decimal("0"), "status": "filled"},
        {"ts": "d2", "symbol": "2330", "side": "buy", "qty": 1000,
         "price": 200.0, "cost": Decimal("0"), "status": "filled"},
        {"ts": "d3", "symbol": "2330", "side": "sell", "qty": 2000,
         "price": 150.0, "cost": Decimal("0"), "status": "filled"},
    ]
    m = report.metrics(BacktestResult(curve, trades, Portfolio(Decimal("1"))))
    assert m["wins"] == 1 and m["losses"] == 1


def test_gated_and_rejected_are_counted_not_filled():
    curve = [("d1", Decimal("1000000")), ("d2", Decimal("1000000"))]
    trades = [
        {"ts": "d1", "symbol": "2330", "side": "buy", "qty": 1000,
         "price": None, "cost": Decimal("0"), "status": "gated"},
        {"ts": "d2", "symbol": "2330", "side": "buy", "qty": 0,
         "price": None, "cost": Decimal("0"), "status": "rejected"},
    ]
    m = report.metrics(BacktestResult(curve, trades, Portfolio(Decimal("1000000"))))
    assert m["num_trades"] == 0  # neither is a filled trade
    assert m["num_gated"] == 1 and m["num_rejected"] == 1
    assert m["total_costs"] == Decimal("0")
