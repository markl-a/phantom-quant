from decimal import Decimal

import pytest

from phantom_quant.backtest.engine import run_backtest
from phantom_quant.bars import Bar
from phantom_quant.driver import BarEvent, BarEventDriver, run_backtest_via_driver
from phantom_quant.strategy import Context, Order, Strategy


def bar(ts: str, close: float = 100.0) -> Bar:
    return Bar(
        ts=ts,
        symbol="2330",
        open=close - 1,
        high=close + 2,
        low=close - 2,
        close=close,
        volume=1000,
    )


class NoOrders(Strategy):
    def on_bar(self, bar: Bar, ctx: Context) -> list[Order]:
        return []


def test_events_are_emitted_in_input_timestamp_order_when_ordered():
    bars = [bar("2026-06-01"), bar("2026-06-02"), bar("2026-06-03")]
    received: list[str] = []

    driver = BarEventDriver(bars)
    driver.register(lambda event: received.append(event.ts))

    assert driver.run() == 3
    assert received == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_multiple_consumers_receive_each_same_event_in_registration_order():
    bars = [bar("2026-06-01"), bar("2026-06-02")]
    calls: list[tuple[str, str, int]] = []

    class NamedConsumer:
        def __init__(self, name: str) -> None:
            self.name = name

        def on_bar(self, event: BarEvent) -> None:
            calls.append((self.name, event.ts, id(event)))

    driver = BarEventDriver(bars)
    first = driver.register(NamedConsumer("first"))
    second = driver.register(NamedConsumer("second"))

    assert first.name == "first"
    assert second.name == "second"
    assert driver.run() == 2
    assert [(name, ts) for name, ts, _ in calls] == [
        ("first", "2026-06-01"),
        ("second", "2026-06-01"),
        ("first", "2026-06-02"),
        ("second", "2026-06-02"),
    ]
    assert calls[0][2] == calls[1][2]
    assert calls[2][2] == calls[3][2]


def test_empty_source_emits_zero_events_and_clock_stays_none():
    driver = BarEventDriver([])

    assert driver.run() == 0
    assert driver.clock is None
    assert driver.event_count == 0


def test_single_bar_advances_clock_to_that_bar_timestamp():
    only = bar("2026-06-01")
    received: list[BarEvent] = []
    driver = BarEventDriver([only])
    driver.register(received.append)

    assert driver.run() == 1
    assert received == [BarEvent.from_bar(only)]
    assert driver.clock == only.ts
    assert driver.event_count == 1


def test_out_of_order_reject_raises_and_sort_mode_emits_sorted():
    bars = [bar("2026-06-02"), bar("2026-06-01"), bar("2026-06-03")]
    rejected = BarEventDriver(bars, on_unordered="reject")

    with pytest.raises(ValueError, match="out-of-order"):
        rejected.run()

    received: list[str] = []
    sorted_driver = BarEventDriver(bars, on_unordered="sort")
    sorted_driver.register(lambda event: received.append(event.ts))

    assert sorted_driver.run() == 3
    assert received == ["2026-06-01", "2026-06-02", "2026-06-03"]
    assert sorted_driver.clock == "2026-06-03"


def test_logical_clock_is_monotonic_and_event_count_matches_emissions():
    bars = [bar("2026-06-01"), bar("2026-06-01"), bar("2026-06-02")]
    seen: list[str] = []
    driver = BarEventDriver(bars)

    def assert_monotonic(event: BarEvent) -> None:
        if seen:
            assert event.ts >= seen[-1]
        seen.append(event.ts)

    driver.register(assert_monotonic)

    assert driver.run() == len(bars)
    assert seen == ["2026-06-01", "2026-06-01", "2026-06-02"]
    assert driver.clock == seen[-1]
    assert driver.event_count == len(bars)


def test_plain_callable_is_accepted_as_consumer():
    received: list[BarEvent] = []
    consumer = received.append
    driver = BarEventDriver([bar("2026-06-01")])

    assert driver.register(consumer) is consumer
    assert driver.run() == 1
    assert received[0].ts == "2026-06-01"
    assert received[0].symbol == "2330"
    assert received[0].bar == bar("2026-06-01")


def test_run_backtest_via_driver_matches_direct_backtest_outputs():
    bars = [
        bar("2026-06-01", close=100.0),
        bar("2026-06-02", close=101.0),
        bar("2026-06-03", close=102.0),
    ]
    cash = Decimal("1000000")

    direct = run_backtest(bars, NoOrders(), cash)
    via_driver = run_backtest_via_driver(bars, NoOrders(), cash)

    assert via_driver.equity_curve == direct.equity_curve
    assert via_driver.trades == direct.trades
