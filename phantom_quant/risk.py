from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from . import costs
from .backtest.engine import BacktestResult, run_backtest
from .data.provider import CsvProvider
from .report import metrics
from .slippage import BpsSlippage, NoSlippage
from .strategies.sma_cross import SmaCross

RISK_SCHEMA_VERSION = 1
PUBLIC_ARTIFACTS = [
    "manifest.json",
    "risk-metrics.json",
    "strategy-comparison.json",
    "summary.md",
]
RISK_METRICS_CONTRACT = [
    "total_return",
    "max_drawdown",
    "annualized_volatility",
    "sharpe",
    "average_exposure",
    "max_exposure",
    "turnover",
]


def _q(value: Decimal, places: str = "0.0001") -> str:
    return str(value.quantize(Decimal(places), ROUND_HALF_UP))


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _status_value(status: Any) -> str:
    return status.value if hasattr(status, "value") else str(status)


def exposure_and_turnover(result: BacktestResult, bars: list[Any]) -> dict[str, str]:
    positions: dict[str, int] = {}
    trades_by_ts: dict[str, list[dict[str, Any]]] = {}
    turnover_notional = Decimal("0")
    for trade in result.trades:
        if _status_value(trade.get("status", "filled")) != "filled":
            continue
        trades_by_ts.setdefault(str(trade["ts"]), []).append(trade)
        if trade["price"] is not None:
            turnover_notional += Decimal(str(trade["price"])) * Decimal(int(trade["qty"]))

    exposure_ratios: list[Decimal] = []
    equity_by_ts = {ts: equity for ts, equity in result.equity_curve}
    for bar in bars:
        for trade in trades_by_ts.get(bar.ts, []):
            qty = int(trade["qty"])
            signed = qty if trade["side"] == "buy" else -qty
            positions[trade["symbol"]] = positions.get(trade["symbol"], 0) + signed
        equity = equity_by_ts.get(bar.ts, Decimal("0"))
        if equity <= 0:
            exposure_ratios.append(Decimal("0"))
            continue
        qty = positions.get(bar.symbol, 0)
        notional = abs(Decimal(qty) * Decimal(str(bar.close)))
        exposure_ratios.append(notional / equity)

    average = (
        sum(exposure_ratios, Decimal("0")) / Decimal(len(exposure_ratios))
        if exposure_ratios
        else Decimal("0")
    )
    maximum = max(exposure_ratios) if exposure_ratios else Decimal("0")
    start_equity = result.equity_curve[0][1] if result.equity_curve else Decimal("0")
    turnover = turnover_notional / start_equity if start_equity else Decimal("0")
    return {
        "average_exposure": _q(average),
        "max_exposure": _q(maximum),
        "turnover": _q(turnover),
    }


def _run_variant(
    *,
    bars: list[Any],
    scenario: str,
    symbol: str,
    short: int,
    long: int,
    cash: str,
    slippage_bps: float,
) -> dict[str, Any]:
    slippage = NoSlippage() if slippage_bps == 0 else BpsSlippage(slippage_bps)
    result = run_backtest(
        bars,
        SmaCross(short=short, long=long, qty=1000),
        cash=Decimal(cash),
        cost_fn=costs.trade_cost,
        slippage=slippage,
    )
    base = metrics(result)
    risk_bits = exposure_and_turnover(result, bars)
    return _jsonable(
        {
            "scenario": scenario,
            "symbol": symbol,
            "strategy": "sma_cross",
            "params": {
                "short": short,
                "long": long,
                "qty": 1000,
                "slippage_bps": slippage_bps,
            },
            "broker": "disabled",
            "data_source": "csv_fixture",
            "investment_advice": False,
            "total_return": base["total_return"],
            "max_drawdown": base["max_drawdown"],
            "annualized_volatility": base["annualized_volatility"],
            "sharpe": base["sharpe"],
            "num_trades": base["num_trades"],
            "num_gated": base["num_gated"],
            "num_rejected": base["num_rejected"],
            **risk_bits,
        }
    )


def build_risk_demo_bundle(
    *,
    csv_path: Path,
    symbol: str,
    short: int,
    long: int,
    cash: str,
) -> dict[str, Any]:
    bars = CsvProvider(str(csv_path)).get_bars(symbol, "1d", "0000-00-00", "9999-99-99")
    runs = [
        _run_variant(
            bars=bars,
            scenario="baseline",
            symbol=symbol,
            short=short,
            long=long,
            cash=cash,
            slippage_bps=0.0,
        ),
        _run_variant(
            bars=bars,
            scenario="slippage_10bps",
            symbol=symbol,
            short=short,
            long=long,
            cash=cash,
            slippage_bps=10.0,
        ),
    ]
    return {
        "manifest": {
            "schema_version": RISK_SCHEMA_VERSION,
            "mode": "offline_risk_metric_demo",
            "data_source": "csv_fixture",
            "broker": "disabled",
            "live_broker_execution": False,
            "real_money": False,
            "investment_advice": False,
            "external_network": False,
            "artifacts": PUBLIC_ARTIFACTS,
        },
        "risk_metrics": {
            "schema_version": RISK_SCHEMA_VERSION,
            "mode": "offline_risk_metric_demo",
            "risk_metrics_contract": RISK_METRICS_CONTRACT,
            "runs": runs,
        },
        "comparison": {
            "schema_version": RISK_SCHEMA_VERSION,
            "mode": "strategy_risk_comparison",
            "ranking_policy": "diagnostic_not_recommendation",
            "winner": None,
            "investment_advice": False,
            "disclaimer": "Offline diagnostic comparison only; not investment advice.",
            "compared_scenarios": [
                {
                    "scenario": row["scenario"],
                    "total_return": row["total_return"],
                    "max_drawdown": row["max_drawdown"],
                    "turnover": row["turnover"],
                    "average_exposure": row["average_exposure"],
                }
                for row in runs
            ],
        },
    }


def render_summary(bundle: dict[str, Any]) -> str:
    lines = [
        "# phantom-quant risk demo",
        "",
        "Offline diagnostic comparison only; not investment advice.",
        "",
        "## Risk metrics",
        "",
    ]
    for row in bundle["risk_metrics"]["runs"]:
        lines.append(
            f"- {row['scenario']}: return {row['total_return']}, "
            f"drawdown {row['max_drawdown']}, exposure avg {row['average_exposure']}, "
            f"turnover {row['turnover']}"
        )
    lines.append("")
    return "\n".join(lines)


def write_risk_demo_bundle(
    csv_path: Path,
    out_dir: Path,
    *,
    symbol: str,
    short: int,
    long: int,
    cash: str,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle = build_risk_demo_bundle(
        csv_path=csv_path,
        symbol=symbol,
        short=short,
        long=long,
        cash=cash,
    )
    payloads = {
        "manifest.json": bundle["manifest"],
        "risk-metrics.json": bundle["risk_metrics"],
        "strategy-comparison.json": bundle["comparison"],
    }
    for name, payload in payloads.items():
        (out_dir / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    (out_dir / "summary.md").write_text(render_summary(bundle), encoding="utf-8")
    return out_dir
