"""Deterministic artifact writers for backtest runs.

Auditable result artifacts: every backtest can write its trade tape, equity
curve, run metadata, and Markdown report to disk as byte-stable files. Byte
stability is the contract the golden tests rely on, so:

  - CSVs are written with the stdlib ``csv`` module, ``lineterminator="\\n"``
    (never platform CRLF) and ``newline=""`` on open.
  - ``run.json`` is ``json.dumps(..., indent=2, sort_keys=True)`` + one trailing
    newline, and NEVER embeds a runtime clock/SHA — those are caller-supplied
    inputs on ``RunMeta`` (clocks and git SHA are not deterministic, so the
    engine accepts them as stamps rather than computing them).
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path

from .backtest.engine import BacktestResult
from .report import metrics, to_markdown

__all__ = ["RunMeta", "to_run_payload", "write_artifacts"]


@dataclass(frozen=True)
class RunMeta:
    symbol: str
    strategy: str
    schema_version: int = 1
    mode: str = "backtest"
    timeframe: str = "1d"
    start: str = ""
    end: str = ""
    cash: str = ""
    params: dict | None = None
    cost_model: str = "tw_stock"
    bar_count: int = 0
    git_sha: str = "unknown"
    version: str = "unknown"
    generated_at: str = ""
    data_source: str = "csv_fixture"
    broker: str = "disabled"


def _decimal_to_str(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _decimal_to_str(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_decimal_to_str(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_decimal_to_str(item) for item in value)
    return value


def _status_value(status) -> str:
    return status.value if hasattr(status, "value") else str(status)


def to_run_payload(result: BacktestResult, meta: RunMeta) -> dict:
    """Build the deterministic JSON payload for a backtest run.

    The whole payload is sanitized through ``_decimal_to_str`` (not just the
    metrics): strategy ``params`` are caller-supplied and, in a codebase where
    money/rates/thresholds are ``Decimal`` end-to-end, may well contain Decimals.
    Sanitizing only ``metrics`` would let a Decimal param reach ``json.dumps`` and
    crash the run with ``TypeError: Object of type Decimal is not JSON serializable``.
    """
    meta_dict = {key: value for key, value in sorted(asdict(meta).items())}
    return _decimal_to_str({
        "meta": meta_dict,
        "metrics": metrics(result),
        "num_bars": len(result.equity_curve),
    })


def write_artifacts(result: BacktestResult, meta: RunMeta, out_dir: str | Path) -> dict[str, Path]:
    """Write deterministic CSV, JSON, and Markdown artifacts for a backtest run."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    trades_path = out_path / "trades.csv"
    equity_path = out_path / "equity.csv"
    run_path = out_path / "run.json"
    report_path = out_path / "report.md"

    with trades_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["ts", "symbol", "side", "qty", "price", "cost", "status", "reason"])
        for trade in result.trades:
            writer.writerow([
                trade["ts"],
                trade["symbol"],
                trade["side"],
                trade["qty"],
                "" if trade["price"] is None else str(trade["price"]),
                str(trade["cost"]),
                _status_value(trade["status"]),
                trade["reason"],
            ])

    with equity_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["ts", "equity"])
        for ts, equity in result.equity_curve:
            writer.writerow([ts, str(equity)])

    payload = to_run_payload(result, meta)
    with run_path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    report = to_markdown(result, {"symbol": meta.symbol, "strategy": meta.strategy})
    with report_path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(report)

    return {
        "trades": trades_path,
        "equity": equity_path,
        "run": run_path,
        "report": report_path,
    }
