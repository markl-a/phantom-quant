# phantom-quant

> **Backtest-only** 台股 (Taiwan stock) trading research engine for the phantom-mesh ecosystem. Event-driven backtester with an accurate 台股 cost model. **Paper and live trading are roadmap, not built.**

What works **today**: feed cached daily bars through an event-driven backtest
engine that fills at the bar close and charges real 台股 現股 fees + 證交稅, then
emit a Markdown report whose every number is independently re-derivable. Backtests
run **fully offline** from a CSV — no broker, no network, no API keys.

What does **not** exist yet (roadmap, see below): paper trading, live order
execution, and any broker integration (Shioaji). The strategy contract is shaped
so the *same* `on_bar` code could later drive paper/live, but that wiring is not
written.

## What's actually built

| Capability | Status |
|---|---|
| Event-driven backtest engine (fill-at-close) | ✅ built |
| Accurate 台股 cost model (fee + 證交稅, min-fee floor) | ✅ built |
| Portfolio accounting (Decimal, average-cost basis, net of costs) | ✅ built |
| SMA crossover strategy (**skeleton, not an edge**) | ✅ built |
| CSV bar provider + parquet cache | ✅ built |
| Markdown backtest report | ✅ built |
| `backtest` CLI command | ✅ built |
| Paper trading | 🗺️ roadmap, not built |
| Live order execution | 🗺️ roadmap, not built |
| Broker integration (Shioaji `fetch` / live provider) | 🗺️ roadmap, not built |

The `broker` optional dependency (`shioaji`) and the `paper`/`live` wording in
some docstrings describe the *intended* direction — there is currently no code
behind them. The only CLI subcommand is `backtest`.

## Highlights

- **Event-driven engine.** Bars are replayed one at a time and the strategy
  reacts via a single `on_bar(bar, ctx)` contract (`phantom_quant/strategy.py`,
  `phantom_quant/backtest/engine.py`). This is the design choice that would let
  the same strategy code run live later — but only the backtest path is wired
  today.
- **Accurate 台股 cost model.** `phantom_quant/costs.py` charges 手續費 0.1425%
  (floored, NT$20 min per side) on every trade and 證交稅 0.3% on sells only,
  with a broker-discount multiplier. Costs are first-class — backtests that skip
  them lie.

## Quickstart

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/python -m pytest -q
.venv/bin/phantom-quant backtest \
  --csv tests/fixtures/sample_2330_1d.csv \
  --strategy sma_cross --symbol 2330 \
  --short 3 --long 6 --cash 1000000 --qty 1000 --out report.md
```

On Windows / PowerShell, use `.\.venv\Scripts\python.exe` and set
`$env:PYTHONUTF8="1"` first.

## Sample output

Running the bundled **synthetic** fixture (`tests/fixtures/sample_2330_1d.csv`,
25 daily bars for 2330) produces a single buy/sell round-trip:

- start equity 1,000,000 → end equity 1,024,574
- **total return: 2.46%**, max drawdown 1.74%, 2 trades (1 closed)

Full numbers, the trade log, the by-hand cost derivation, and an equity-curve
chart are in [`docs/sample-report.md`](docs/sample-report.md).

> ⚠️ **The SMA crossover is a skeleton, not a profitable strategy.** The positive
> return on the fixture is an artifact of synthetic data hand-built to fire one
> round-trip — it is not evidence of an edge and is not investment advice. The
> point of this project is the engine and the cost model, not the strategy.
