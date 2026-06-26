from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from . import costs, limit_lock
from .backtest.engine import BacktestResult, run_backtest
from .bars import Bar
from .data.provider import CsvProvider
from .paper import run_paper
from .report import metrics
from .strategies.sma_cross import SmaCross

TW_SCENARIO_SCHEMA_VERSION = 1
PUBLIC_ARTIFACTS = [
    "manifest.json",
    "tw-rules.json",
    "parity.json",
    "summary.md",
]


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


def _trade_rows(result: BacktestResult) -> list[dict[str, Any]]:
    return [
        {
            "ts": row["ts"],
            "symbol": row["symbol"],
            "side": row["side"],
            "qty": row["qty"],
            "price": row["price"],
            "cost": row["cost"],
            "status": row["status"],
            "reason": row["reason"],
        }
        for row in result.trades
    ]


def _equity_rows(result: BacktestResult) -> list[dict[str, Any]]:
    return [{"ts": ts, "equity": equity} for ts, equity in result.equity_curve]


def _run_metrics(result: BacktestResult) -> dict[str, Any]:
    return _jsonable(metrics(result))


def manifest() -> dict[str, Any]:
    return {
        "schema_version": TW_SCENARIO_SCHEMA_VERSION,
        "mode": "taiwan_rule_reproducibility_scenario",
        "data_source": "csv_fixture",
        "broker": "disabled",
        "live_broker_execution": False,
        "real_money": False,
        "investment_advice": False,
        "external_network": False,
        "artifacts": PUBLIC_ARTIFACTS,
    }


def tw_rules_artifact() -> dict[str, Any]:
    locked_up = Bar("2026-01-02", "2330", 110.0, 110.0, 110.0, 110.0, 1000)
    locked_down = Bar("2026-01-03", "2330", 90.0, 90.0, 90.0, 90.0, 1000)
    tick_prices = ["9.99", "10", "50", "100", "500", "1000"]
    return {
        "schema_version": TW_SCENARIO_SCHEMA_VERSION,
        "mode": "taiwan_stock_rule_snapshot",
        "rule_scope": "offline_research_fixture",
        "investment_advice": False,
        "fee_model": {
            "fee_rate": str(costs.FEE_RATE),
            "tax_rate": str(costs.TAX_RATE),
            "minimum_fee": str(costs.MIN_FEE),
            "lot_size": costs.LOT_SIZE,
        },
        "tick_size_examples": [
            {"price": price, "tick_size": str(costs.tick_size(float(price)))}
            for price in tick_prices
        ],
        "cost_examples": {
            "buy_2330_1000_at_600": str(costs.trade_cost("buy", 600.0, 1000)),
            "sell_2330_1000_at_600": str(costs.trade_cost("sell", 600.0, 1000)),
        },
        "limit_band_example": {
            "prev_close": "100",
            "floor": "90.0",
            "ceiling": "110.0",
        },
        "limit_lock_examples": {
            "limit_up_buy_blocked": limit_lock.lock_blocks("buy", locked_up, 100.0),
            "limit_down_sell_blocked": limit_lock.lock_blocks("sell", locked_down, 100.0),
        },
    }


def parity_artifact(
    *,
    csv_path: Path,
    symbol: str,
    short: int,
    long: int,
    cash: str,
) -> dict[str, Any]:
    bars = CsvProvider(str(csv_path)).get_bars(symbol, "1d", "0000-00-00", "9999-99-99")
    strategy_args = {"short": short, "long": long, "qty": 1000}
    backtest = run_backtest(
        bars,
        SmaCross(**strategy_args),
        cash=Decimal(cash),
        cost_fn=costs.trade_cost,
    )
    paper = run_paper(
        bars,
        SmaCross(**strategy_args),
        cash=Decimal(cash),
        cost_fn=costs.trade_cost,
    )
    backtest_trades = _jsonable(_trade_rows(backtest))
    paper_trades = _jsonable(_trade_rows(paper))
    backtest_equity = _jsonable(_equity_rows(backtest))
    paper_equity = _jsonable(_equity_rows(paper))
    backtest_metrics = _run_metrics(backtest)
    paper_metrics = _run_metrics(paper)
    run_meta = {
        "symbol": symbol,
        "strategy": "sma_cross",
        "timeframe": "1d",
        "start": "0000-00-00",
        "end": "9999-99-99",
        "cash": cash,
        "params": strategy_args,
        "cost_model": "tw_stock",
        "bar_count": len(bars),
        "git_sha": "DEMO",
        "version": "0.1.0a0",
        "generated_at": "2026-06-26T00:00:00Z",
        "data_source": "csv_fixture",
        "broker": "disabled",
    }
    return {
        "schema_version": TW_SCENARIO_SCHEMA_VERSION,
        "mode": "backtest_paper_reproducibility_parity",
        "symbol": symbol,
        "strategy": "sma_cross",
        "broker": "disabled",
        "live_broker_execution": False,
        "real_money": False,
        "investment_advice": False,
        "data_source": "csv_fixture",
        "disclaimer": "Offline research scenario only; not investment advice.",
        "reproducibility": run_meta,
        "backtest": {
            "num_bars": len(bars),
            "num_trades": backtest_metrics["num_trades"],
            "metrics": backtest_metrics,
        },
        "paper": {
            "num_bars": len(bars),
            "num_trades": paper_metrics["num_trades"],
            "metrics": paper_metrics,
        },
        "parity": {
            "trades_match": backtest_trades == paper_trades,
            "equity_match": backtest_equity == paper_equity,
            "metrics_match": backtest_metrics == paper_metrics,
            "run_meta_diff": ["mode"],
        },
    }


def build_tw_scenario_bundle(
    *,
    csv_path: Path,
    symbol: str,
    short: int,
    long: int,
    cash: str,
) -> dict[str, Any]:
    return {
        "manifest": manifest(),
        "rules": tw_rules_artifact(),
        "parity": parity_artifact(
            csv_path=csv_path,
            symbol=symbol,
            short=short,
            long=long,
            cash=cash,
        ),
    }


def render_summary(bundle: dict[str, Any]) -> str:
    parity = bundle["parity"]["parity"]
    rules = bundle["rules"]
    lines = [
        "# phantom-quant Taiwan rule reproducibility scenario",
        "",
        "Offline research scenario only; not investment advice.",
        "",
        "## Taiwan Rule Snapshot",
        "",
        f"- fee rate: {rules['fee_model']['fee_rate']}",
        f"- sell tax rate: {rules['fee_model']['tax_rate']}",
        f"- buy cost example: {rules['cost_examples']['buy_2330_1000_at_600']}",
        f"- sell cost example: {rules['cost_examples']['sell_2330_1000_at_600']}",
        "",
        "## Backtest / Paper Parity",
        "",
        f"- trades match: {parity['trades_match']}",
        f"- equity match: {parity['equity_match']}",
        f"- metrics match: {parity['metrics_match']}",
        "",
    ]
    return "\n".join(lines)


def write_tw_scenario_bundle(
    *,
    csv_path: Path,
    out_dir: Path,
    symbol: str,
    short: int,
    long: int,
    cash: str,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle = build_tw_scenario_bundle(
        csv_path=csv_path,
        symbol=symbol,
        short=short,
        long=long,
        cash=cash,
    )
    payloads = {
        "manifest.json": bundle["manifest"],
        "tw-rules.json": bundle["rules"],
        "parity.json": bundle["parity"],
    }
    for name, payload in payloads.items():
        (out_dir / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    (out_dir / "summary.md").write_text(render_summary(bundle), encoding="utf-8")
    return out_dir
