"""Bar-clocked event driver for Phantom Quant.

The driver turns each :class:`phantom_quant.bars.Bar` into one immutable
``BarEvent`` and dispatches that same event object to registered consumers in
registration order. Consumers may implement the ``BarConsumer`` protocol with
``on_bar(event)`` or be plain callables accepting a ``BarEvent``.

Open question: the existing engine consumes a list, not a stream, so
``run_backtest_via_driver`` buffers bars with ``CollectingConsumer`` and then
calls ``run_backtest``. A future streaming paper/live engine would consume
``BarEvent`` objects directly through ``on_bar``. The clock here is a simulated
logical clock based on each event timestamp, not real-time scheduling.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol, TypeVar

from phantom_quant.backtest.engine import BacktestResult, run_backtest
from phantom_quant.bars import Bar
from phantom_quant.strategy import Strategy


@dataclass(frozen=True)
class BarEvent:
    ts: str
    symbol: str
    bar: Bar

    @classmethod
    def from_bar(cls, bar: Bar) -> BarEvent:
        return cls(ts=bar.ts, symbol=bar.symbol, bar=bar)


class BarConsumer(Protocol):
    def on_bar(self, event: BarEvent) -> None:
        pass


Consumer = BarConsumer | Callable[[BarEvent], None]
ConsumerT = TypeVar("ConsumerT", bound=Consumer)


class BarEventDriver:
    def __init__(self, source: Iterable[Bar], *, on_unordered: str = "reject") -> None:
        if on_unordered not in {"reject", "sort"}:
            raise ValueError("on_unordered must be 'reject' or 'sort'")

        self._on_unordered = on_unordered
        self._source = sorted(source, key=lambda bar: bar.ts) if on_unordered == "sort" else source
        self._consumers: list[Consumer] = []
        self._clock: str | None = None
        self._event_count = 0

    def register(self, consumer: ConsumerT) -> ConsumerT:
        self._consumers.append(consumer)
        return consumer

    @property
    def clock(self) -> str | None:
        return self._clock

    @property
    def event_count(self) -> int:
        return self._event_count

    def run(self) -> int:
        for bar in self._source:
            event = BarEvent.from_bar(bar)
            if self._on_unordered == "reject" and self._clock is not None and bar.ts < self._clock:
                raise ValueError(f"out-of-order bar timestamp {bar.ts!r} after {self._clock!r}")

            self._clock = bar.ts
            for consumer in self._consumers:
                on_bar = getattr(consumer, "on_bar", None)
                if on_bar is not None:
                    on_bar(event)
                else:
                    consumer(event)
            self._event_count += 1

        return self._event_count


@dataclass
class CollectingConsumer:
    bars: list[Bar] = field(default_factory=list)

    def on_bar(self, event: BarEvent) -> None:
        self.bars.append(event.bar)


def run_backtest_via_driver(
    source: Iterable[Bar],
    strategy: Strategy,
    cash: Decimal,
    **kw: object,
) -> BacktestResult:
    driver = BarEventDriver(source)
    consumer = driver.register(CollectingConsumer())
    driver.run()
    return run_backtest(consumer.bars, strategy, cash, **kw)
