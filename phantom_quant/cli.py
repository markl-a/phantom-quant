"""phantom-quant CLI.

  phantom-quant backtest --csv tests/fixtures/sample_2330_1d.csv \
      --strategy sma_cross --symbol 2330 --short 3 --long 6 --cash 1000000 --out report.md

`backtest` is the only command and runs entirely offline from --csv. A live
`fetch` (Shioaji) command and paper/live execution are roadmap items, not built.
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

from . import costs, report
from .backtest.engine import run_backtest
from .data.provider import CsvProvider
from .strategies.sma_cross import SmaCross

_STRATEGIES = {"sma_cross": SmaCross}


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
    bt.add_argument("--out", required=True, type=Path)

    args = parser.parse_args(argv)

    if args.cmd == "backtest":
        if args.strategy not in _STRATEGIES:
            print(f"unknown strategy: {args.strategy}. choices: {sorted(_STRATEGIES)}",
                  file=sys.stderr)
            return 2
        bars = CsvProvider(args.csv).get_bars(args.symbol, args.timeframe, args.start, args.end)
        if not bars:
            print("no bars for that symbol/range", file=sys.stderr)
            return 2
        strategy = _STRATEGIES[args.strategy](short=args.short, long=args.long, qty=args.qty)
        result = run_backtest(bars, strategy,
                              cash=Decimal(args.cash), cost_fn=costs.trade_cost)
        md = report.to_markdown(result, {"symbol": args.symbol, "strategy": args.strategy})
        args.out.write_text(md, encoding="utf-8")
        print(f"report written: {args.out}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
