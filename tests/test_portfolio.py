from decimal import Decimal

from phantom_quant.portfolio import Portfolio


def test_buy_then_sell_tracks_cash_positions_and_realized_pnl():
    p = Portfolio(cash=Decimal("1000000"))
    # buy 1000 @ 100, cost(fee) 142 -> cash = 1000000 - 100000 - 142
    p.apply_fill("buy", "2330", 1000, 100.0, Decimal("142"))
    assert p.positions["2330"] == 1000
    assert p.cash == Decimal("899858")
    # sell 1000 @ 110, cost(fee+tax) 466 -> proceeds 110000 - 466
    p.apply_fill("sell", "2330", 1000, 110.0, Decimal("466"))
    assert p.positions.get("2330", 0) == 0
    assert p.cash == Decimal("1009392")
    # realized = proceeds_net - cost_basis_net = (110000-466) - (100000+142) = 9392
    assert p.realized == Decimal("9392")


def test_equity_is_cash_plus_marked_positions():
    p = Portfolio(cash=Decimal("1000000"))
    p.apply_fill("buy", "2330", 1000, 100.0, Decimal("142"))
    eq = p.equity({"2330": 105.0})
    assert eq == Decimal("899858") + Decimal("105000")
