from __future__ import annotations

from decimal import Decimal

from phantom_quant import costs
from phantom_quant.backtest.engine import BacktestResult, run_backtest
from phantom_quant.backtest.execution import FillStatus
from phantom_quant.bars import Bar
from phantom_quant.driver import BarEventDriver
from phantom_quant.paper import PaperAccount, PaperBroker, run_paper
from phantom_quant.slippage import BpsSlippage
from phantom_quant.strategy import Context, Order, Strategy


def _bar(ts: str, close: float = 100.0, symbol: str = "2330") -> Bar:
    return Bar(
        ts=ts,
        symbol=symbol,
        open=close - 1,
        high=close + 2,
        low=close - 2,
        close=close,
        volume=1000,
    )


def _single_symbol_bars() -> list[Bar]:
    return [
        _bar("2026-06-01", close=100.0),
        _bar("2026-06-02", close=105.0),
        _bar("2026-06-03", close=110.0),
    ]


class NoOrders(Strategy):
    def on_bar(self, bar: Bar, ctx: Context) -> list[Order]:
        return []


class ScriptedOrders(Strategy):
    def __init__(self, orders_by_bar: dict[tuple[str, str], list[Order]]) -> None:
        self._orders_by_bar = orders_by_bar

    def on_bar(self, bar: Bar, ctx: Context) -> list[Order]:
        return list(self._orders_by_bar.get((bar.ts, bar.symbol), []))


def _buy_then_sell_strategy() -> ScriptedOrders:
    return ScriptedOrders(
        {
            ("2026-06-01", "2330"): [Order("2330", "buy", 1000)],
            ("2026-06-03", "2330"): [Order("2330", "sell", 1000)],
        }
    )


def _assert_same_result(left: BacktestResult, right: BacktestResult) -> None:
    assert left.equity_curve == right.equity_curve
    assert left.trades == right.trades
    assert left.portfolio.cash == right.portfolio.cash
    assert left.portfolio.positions == right.portfolio.positions
    assert left.portfolio.realized == right.portfolio.realized


def test_paper_equals_backtest_default():
    bars = _single_symbol_bars()
    cash = Decimal("1000000")

    backtest = run_backtest(bars, _buy_then_sell_strategy(), cash)
    paper = run_paper(bars, _buy_then_sell_strategy(), cash)

    _assert_same_result(paper, backtest)


def test_paper_equals_backtest_with_slippage_and_cost():
    bars = _single_symbol_bars()
    cash = Decimal("1000000")

    backtest = run_backtest(
        bars,
        _buy_then_sell_strategy(),
        cash,
        cost_fn=costs.trade_cost,
        slippage=BpsSlippage(25),
    )
    paper = run_paper(
        bars,
        _buy_then_sell_strategy(),
        cash,
        cost_fn=costs.trade_cost,
        slippage=BpsSlippage(25),
    )

    _assert_same_result(paper, backtest)


def test_account_updates_across_multibar_run():
    bars = _single_symbol_bars()
    account = PaperAccount(Decimal("1000000"))
    broker = PaperBroker(_buy_then_sell_strategy(), account)
    driver = BarEventDriver(bars)
    driver.register(broker)

    driver.run()

    assert account.cash == Decimal("1009372")
    assert account.positions == {}
    assert account.realized_pnl == Decimal("9372")
    assert account.equity() == Decimal("1009372")


def test_no_fill_on_no_signal_bar():
    bars = _single_symbol_bars()

    result = run_paper(bars, NoOrders(), Decimal("1000000"))

    assert result.trades == []
    assert not any(trade["status"] is FillStatus.FILLED for trade in result.trades)
    assert len(result.equity_curve) == len(bars)


def test_equity_marked_each_bar():
    bars = _single_symbol_bars()
    account = PaperAccount(Decimal("1000000"))
    broker = PaperBroker(NoOrders(), account)
    driver = BarEventDriver(bars)
    driver.register(broker)

    driver.run()

    assert len(account.equity_curve) == len(bars)


def test_multi_symbol_run():
    bars = [
        _bar("2026-06-01", close=50.0, symbol="AAA"),
        _bar("2026-06-01", close=20.0, symbol="BBB"),
        _bar("2026-06-02", close=55.0, symbol="AAA"),
        _bar("2026-06-02", close=24.0, symbol="BBB"),
    ]
    def strategy() -> ScriptedOrders:
        return ScriptedOrders(
            {
                ("2026-06-01", "AAA"): [Order("AAA", "buy", 1000)],
                ("2026-06-01", "BBB"): [Order("BBB", "buy", 1000)],
            }
        )

    cash = Decimal("1000000")
    backtest = run_backtest(bars, strategy(), cash)

    account = PaperAccount(cash)
    broker = PaperBroker(strategy(), account)
    driver = BarEventDriver(bars)
    driver.register(broker)
    driver.run()
    paper = BacktestResult(
        equity_curve=account.equity_curve,
        trades=account.trades,
        portfolio=account.portfolio,
    )

    _assert_same_result(paper, backtest)
    assert account.positions == {"AAA": 1000, "BBB": 1000}
