from decimal import Decimal

from phantom_quant import costs


def test_tick_size_bands():
    assert costs.tick_size(9.5) == Decimal("0.01")
    assert costs.tick_size(25) == Decimal("0.05")
    assert costs.tick_size(80) == Decimal("0.1")
    assert costs.tick_size(300) == Decimal("0.5")
    assert costs.tick_size(800) == Decimal("1")
    assert costs.tick_size(1200) == Decimal("5")


def test_fee_is_floored_to_integer_with_minimum():
    # 100 * 1000 * 0.001425 = 142.5 -> floor 142
    assert costs.fee(100.0, 1000) == Decimal("142")
    # tiny trade hits the NT$20 minimum: 10 * 100 * 0.001425 = 1.425 -> min 20
    assert costs.fee(10.0, 100) == Decimal("20")


def test_tax_only_sums_for_sells_via_trade_cost():
    # buy: fee only. 100*1000*0.001425=142.5->142 ; tax=0
    assert costs.trade_cost("buy", 100.0, 1000) == Decimal("142")
    # sell: fee 142 + tax floor(100*1000*0.003=300)=300 -> 442
    assert costs.trade_cost("sell", 100.0, 1000) == Decimal("442")
