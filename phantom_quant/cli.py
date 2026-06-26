"""phantom-quant CLI (P0).

  phantom-quant backtest --csv tests/fixtures/sample_2330_1d.csv \
      --strategy sma_cross --symbol 2330 --short 3 --long 6 --cash 1000000 --out report.md

`fetch` (Shioaji live pull) is P0+ and only works with the optional `broker`
extra installed; v1 backtests run entirely offline from --csv.
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

from . import costs, report, risk, tw_scenario
from .artifacts import RunMeta, write_artifacts
from .backtest.engine import run_backtest
from .data.provider import CachedProvider, CsvProvider
from .data import store
from .slippage import BpsSlippage, NoSlippage
from .strategies.sma_cross import SmaCross
from .validation import BarValidationError, validate_bars
from .paper import run_paper
from .registry import StrategyError, load_strategy

_STRATEGIES = {"sma_cross": SmaCross}


def _resolve_strategy(args):
    try:
        return load_strategy(args.strategy, short=args.short, long=args.long, qty=args.qty)
    except StrategyError as exc:
        print(str(exc), file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="phantom-quant")
    sub = parser.add_subparsers(dest="cmd", required=True)

    bt = sub.add_parser("backtest", help="run an offline backtest from a CSV")
    bt.add_argument("--csv", required=True, type=Path)
    bt.add_argument("--strategy", required=True)
    bt.add_argument("--symbol", required=True)
    bt.add_argument("--timeframe", default="1d")
    bt.add_argument("--start", default="0000-00-00")
    bt.add_argument("--end", default="9999-99-99")
    bt.add_argument("--cash", default="1000000")
    bt.add_argument("--short", type=int, default=5, help="short SMA window")
    bt.add_argument("--long", type=int, default=20, help="long SMA window")
    bt.add_argument("--qty", type=int, default=1000, help="shares per order")
    bt.add_argument("--slippage-bps", type=float, default=0.0,
                    help="adverse slippage in basis points (1 bp = 0.01%%); "
                         "0 = no slippage (default)")
    bt.add_argument("--no-validate", action="store_true",
                    help="skip structural bar validation (OHLC sanity, ordering, "
                         "duplicates); validation is ON by default")
    bt.add_argument("--cache", type=Path, default=None,
                    help="Parquet cache directory; bars for this "
                         "symbol/timeframe/range are fetched once then reused")
    bt.add_argument("--out", required=True, type=Path)
    bt.add_argument("--artifacts", type=Path, default=None,
                    help="directory to write auditable artifacts "
                         "(trades.csv, equity.csv, run.json, report.md)")
    # Determinism stamps: passed IN, never computed at runtime (clocks/SHA are
    # not reproducible). Leave blank for byte-stable golden runs.
    bt.add_argument("--git-sha", default="unknown",
                    help="git commit stamp recorded in run.json (caller-supplied)")
    bt.add_argument("--version", default="unknown",
                    help="version stamp recorded in run.json (caller-supplied)")
    bt.add_argument("--generated-at", default="",
                    help="ISO timestamp recorded in run.json (caller-supplied; "
                         "left blank keeps artifacts byte-stable)")

    pp = sub.add_parser("paper", help="run simulated paper trading from a CSV")
    pp.add_argument("--csv", required=True, type=Path)
    pp.add_argument("--strategy", required=True)
    pp.add_argument("--symbol", required=True)
    pp.add_argument("--timeframe", default="1d")
    pp.add_argument("--start", default="0000-00-00")
    pp.add_argument("--end", default="9999-99-99")
    pp.add_argument("--cash", default="1000000")
    pp.add_argument("--short", type=int, default=5, help="short SMA window")
    pp.add_argument("--long", type=int, default=20, help="long SMA window")
    pp.add_argument("--qty", type=int, default=1000, help="shares per order")
    pp.add_argument("--slippage-bps", type=float, default=0.0,
                    help="adverse slippage in basis points (1 bp = 0.01%%); "
                         "0 = no slippage (default)")
    pp.add_argument("--no-validate", action="store_true",
                    help="skip structural bar validation (OHLC sanity, ordering, "
                         "duplicates); validation is ON by default")
    pp.add_argument("--cache", type=Path, default=None,
                    help="Parquet cache directory; bars for this "
                         "symbol/timeframe/range are fetched once then reused")
    pp.add_argument("--out", required=True, type=Path)
    pp.add_argument("--artifacts", type=Path, default=None,
                    help="directory to write auditable paper artifacts "
                         "(trades.csv, equity.csv, run.json, report.md)")
    pp.add_argument("--git-sha", default="unknown",
                    help="git commit stamp recorded in run.json (caller-supplied)")
    pp.add_argument("--version", default="unknown",
                    help="version stamp recorded in run.json (caller-supplied)")
    pp.add_argument("--generated-at", default="",
                    help="ISO timestamp recorded in run.json (caller-supplied; "
                         "left blank keeps artifacts byte-stable)")

    ic = sub.add_parser("import-csv",
                        help="load a local CSV into the Parquet cache schema")
    ic.add_argument("--csv", required=True, type=Path)
    ic.add_argument("--symbol", required=True)
    ic.add_argument("--timeframe", default="1d")
    ic.add_argument("--start", default="0000-00-00")
    ic.add_argument("--end", default="9999-99-99")
    ic.add_argument("--out", required=True, type=Path)

    rd = sub.add_parser(
        "risk-demo",
        help="write an offline risk-metric and strategy-comparison artifact bundle",
    )
    rd.add_argument("--csv", required=True, type=Path)
    rd.add_argument("--symbol", required=True)
    rd.add_argument("--short", type=int, default=3)
    rd.add_argument("--long", type=int, default=6)
    rd.add_argument("--cash", default="1000000")
    rd.add_argument("--out", required=True, type=Path)

    tw = sub.add_parser(
        "tw-scenario",
        help="write a Taiwan-rule and backtest/paper reproducibility scenario bundle",
    )
    tw.add_argument("--csv", required=True, type=Path)
    tw.add_argument("--symbol", required=True)
    tw.add_argument("--short", type=int, default=3)
    tw.add_argument("--long", type=int, default=6)
    tw.add_argument("--cash", default="1000000")
    tw.add_argument("--out", required=True, type=Path)

    args = parser.parse_args(argv)

    if args.cmd == "backtest":
        # Resolve strategy first (registry path) so an unknown strategy fails
        # before any CSV is read -- preserving the original backtest ordering.
        strategy = _resolve_strategy(args)
        if strategy is None:
            return 2
        provider = CsvProvider(args.csv)
        if args.cache is not None:
            provider = CachedProvider(provider, args.cache)
        bars = provider.get_bars(args.symbol, args.timeframe, args.start, args.end)
        if not bars:
            print("no bars for that symbol/range", file=sys.stderr)
            return 2
        if not args.no_validate:
            try:
                validate_bars(bars, symbol=args.symbol)
            except BarValidationError as e:
                print(f"bar data failed validation: {e}", file=sys.stderr)
                return 2
        slip = NoSlippage() if args.slippage_bps == 0 else BpsSlippage(bps=args.slippage_bps)
        result = run_backtest(bars, strategy,
                              cash=Decimal(args.cash), cost_fn=costs.trade_cost,
                              slippage=slip)
        md = report.to_markdown(result, {"symbol": args.symbol, "strategy": args.strategy})
        args.out.write_text(md, encoding="utf-8")
        print(f"report written: {args.out}")
        if args.artifacts is not None:
            meta = RunMeta(
                symbol=args.symbol, strategy=args.strategy, timeframe=args.timeframe,
                mode="backtest",
                start=args.start, end=args.end, cash=str(args.cash),
                params={"short": args.short, "long": args.long, "qty": args.qty,
                        "slippage_bps": args.slippage_bps},
                bar_count=len(bars), git_sha=args.git_sha,
                version=args.version, generated_at=args.generated_at)
            paths = write_artifacts(result, meta, args.artifacts)
            print(f"artifacts written: {args.artifacts} "
                  f"({', '.join(p.name for p in paths.values())})")
        return 0

    if args.cmd == "paper":
        strategy = _resolve_strategy(args)
        if strategy is None:
            return 2
        provider = CsvProvider(args.csv)
        if args.cache is not None:
            provider = CachedProvider(provider, args.cache)
        bars = provider.get_bars(args.symbol, args.timeframe, args.start, args.end)
        if not bars:
            print("no bars for that symbol/range", file=sys.stderr)
            return 2
        if not args.no_validate:
            try:
                validate_bars(bars, symbol=args.symbol)
            except BarValidationError as e:
                print(f"bar data failed validation: {e}", file=sys.stderr)
                return 2
        slip = NoSlippage() if args.slippage_bps == 0 else BpsSlippage(bps=args.slippage_bps)
        result = run_paper(bars, strategy, cash=Decimal(args.cash),
                           cost_fn=costs.trade_cost, slippage=slip)
        md = report.to_markdown(result, {"symbol": args.symbol, "strategy": args.strategy})
        args.out.write_text(md, encoding="utf-8")
        print(f"report written: {args.out}")
        if args.artifacts is not None:
            meta = RunMeta(
                symbol=args.symbol, strategy=args.strategy, timeframe=args.timeframe,
                mode="paper",
                start=args.start, end=args.end, cash=str(args.cash),
                params={"short": args.short, "long": args.long, "qty": args.qty,
                        "slippage_bps": args.slippage_bps},
                bar_count=len(bars), git_sha=args.git_sha,
                version=args.version, generated_at=args.generated_at)
            paths = write_artifacts(result, meta, args.artifacts)
            print(f"artifacts written: {args.artifacts} "
                  f"({', '.join(p.name for p in paths.values())})")
        return 0

    if args.cmd == "import-csv":
        bars = CsvProvider(args.csv).get_bars(args.symbol, args.timeframe,
                                              args.start, args.end)
        if not bars:
            print(f"no rows for symbol {args.symbol!r} in {args.csv}", file=sys.stderr)
            return 2
        store.save_bars(bars, args.out)
        print(f"imported {len(bars)} bars for {args.symbol} -> {args.out}")
        return 0

    if args.cmd == "risk-demo":
        out_dir = risk.write_risk_demo_bundle(
            args.csv,
            args.out,
            symbol=args.symbol,
            short=args.short,
            long=args.long,
            cash=args.cash,
        )
        print(
            json.dumps(
                {"out_dir": str(out_dir), "artifacts": risk.PUBLIC_ARTIFACTS},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.cmd == "tw-scenario":
        out_dir = tw_scenario.write_tw_scenario_bundle(
            csv_path=args.csv,
            out_dir=args.out,
            symbol=args.symbol,
            short=args.short,
            long=args.long,
            cash=args.cash,
        )
        print(
            json.dumps(
                {"out_dir": str(out_dir), "artifacts": tw_scenario.PUBLIC_ARTIFACTS},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
