from phantom_quant.bars import Bar


def test_bar_is_frozen_and_holds_ohlcv():
    b = Bar(ts="2026-06-01", symbol="2330", open=900.0, high=910.0,
            low=895.0, close=905.0, volume=12000)
    assert b.close == 905.0 and b.symbol == "2330"
    import dataclasses
    try:
        b.close = 1.0  # type: ignore[misc]
        assert False, "Bar should be frozen"
    except dataclasses.FrozenInstanceError:
        pass
