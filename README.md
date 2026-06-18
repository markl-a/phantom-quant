# phantom-quant

> 台股 backtest → paper → live trading engine for the phantom-mesh ecosystem. Offline backtesting with auditable, re-derivable numbers — no broker, no real money.

Backtests run **fully offline** from cached bar data — no broker, no network.

- **Status** (what's shipped / planned): see [ROADMAP.md](ROADMAP.md).
- **All docs**: see [docs/INDEX.md](docs/INDEX.md).

## Quickstart (Windows / PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
$env:PYTHONUTF8="1"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\phantom-quant.exe backtest --csv tests\fixtures\sample_2330_1d.csv --strategy sma_cross --symbol 2330 --short 3 --long 6 --cash 1000000 --out report.md
```

The demo prints a real backtest: total return **2.46%**, max drawdown 1.74%, 2 trades (one buy/sell round-trip) on the bundled 2330 fixture — every number re-derivable from the equity curve, with 台股 fees/tax charged. `--short`/`--long` tune the SMA windows (default 5/20).

## Backtest options

| flag | effect |
|------|--------|
| `--slippage-bps N` | adverse slippage of N basis points (buy fills higher, sell lower), clamped into the bar's traded range. `0` = frictionless (default). |
| `--cache DIR` | Parquet cache: fetch a symbol/timeframe/range once, reuse it on later runs. |
| `--no-validate` | skip structural bar validation (OHLC sanity, ordering, duplicates, finite/positive prices). Validation is **on by default** — bad data fails loud (`rc=2`), it never runs a backtest on quietly-wrong bars. |
| `--artifacts DIR` | also write auditable artifacts (see below). |

## Auditable result artifacts

`--artifacts DIR` writes a **byte-stable** record of the run:

- `trades.csv` — the full trade tape (`ts,symbol,side,qty,price,cost,status,reason`), including gated/rejected orders.
- `equity.csv` — the mark-to-market equity curve (`ts,equity`).
- `run.json` — run metadata (symbol, strategy, params, cash, date range) + every metric (return, drawdown, realized PnL, costs paid, win/loss, gated/rejected counts).
- `report.md` — the human-readable summary.

The files are deterministic: LF line endings, sorted/indented JSON, and **no runtime clock or git SHA is ever computed** — pass `--git-sha`/`--version`/`--generated-at` in if you want them stamped, so the output stays reproducible. A golden test pins the bytes of a fixed backtest; regenerate intentionally with `PHANTOM_QUANT_UPDATE_GOLDEN=1 pytest tests/test_artifacts.py`.

```powershell
.\.venv\Scripts\phantom-quant.exe backtest --csv tests\fixtures\sample_2330_1d.csv `
    --strategy sma_cross --symbol 2330 --short 3 --long 6 --cash 1000000 `
    --slippage-bps 10 --cache .\cache --artifacts .\run --out report.md
```

