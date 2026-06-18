# Roadmap

> **This file is the single source of truth for project status.** Other docs (README, `docs/INDEX.md`) link here instead of keeping their own status lists.
>
> _Last updated: 2026-06-19._

phantom-quant is a 台股 (Taiwan-stock) **backtest → paper → live** trading engine for the phantom-mesh ecosystem. Today it ships **P0 (offline data + backtest)** plus a hermetic **simulated paper-trading** core. No live broker, no real money, no network at runtime.

Each "Shipped" item below is grounded in a real merge on `master` (commit SHA shown). Numbers (test counts, returns) are taken from the merge messages and the bundled fixture — nothing is invented.

## Shipped

Foundations (P0 — `master` @ `d02f2da` and earlier):
- **Domain primitives** — frozen OHLCV `Bar`, `Decimal` portfolio (positions / cash / realized-PnL), 台股 fee/tax/tick **cost model**, event-driven `Strategy`/`Order`/`Context` contract. (`425387b`, `7e35ada`, `acf843b`, `fdd7a11`)
- **Data layer** — `BarProvider` ABC, offline `CsvProvider`, Parquet bar store (save/load roundtrip), bundled `2330` fixture. (`b023cd3`, `5ef4576`)
- **SMA-crossover strategy** + event-driven backtest engine (fill-at-close, costs charged). (`275e93d`, `e47e22f`)
- **CLI `backtest`** command writing a markdown report from data-derived metrics; `--short/--long/--qty` for a real round-trip demo. (`16a81a1`, `4fd18c1`, `d32af06`)
- **Fill gating** by order-status validation + marketable-limit-fill clamp into the bar's traded range. (`fc921e9`, `90e7544`)
- **`CachedProvider` + Parquet validation + `import-csv` CLI.** (`9380c6d`)

Hardening & auditability (P1–P3 — `master` @ `7a25d12`, the "final form" merge):
- **Auditable, byte-stable artifacts** (`--artifacts DIR`): `trades.csv`, `equity.csv`, `run.json`, `report.md`; deterministic (LF endings, sorted/indented JSON, no runtime clock/SHA), golden-byte tested. (`10e8b94`)
- **Slippage model** (`--slippage-bps`) + multi-symbol equity fix + cross-symbol fill guard. (`a70744b`)
- **Structural data validation** on by default — bad bars fail loud (`rc=2`), never silently backtested (`--no-validate` to skip). (`a1ae299`)
- **Richer metrics** — PnL, costs, gated/rejected counts, quantity-aware win/loss. (`b0b1bb4`)
- **`--cache` wired into backtest** + README docs for slippage/cache/validation/artifacts. (`f1c6fdc`, `a328383`)
- **台股 ±10% 漲跌停 limit-lock** fill gating. (`e2aa7bb`)
  - This sub-line grew the suite from 44 → **99 passing tests**.

Event/paper/registry seams (additive, P2–P3):
- **`BarEventDriver`** — bar-clocked event stream that composes with `run_backtest` (identical results), the prerequisite for paper/live. (`2401771` → merge `e317fa9`; 99 → **107** tests)
- **Hermetic simulated paper-trading core** — `PaperBroker`/`PaperAccount` consume the driver stream and delegate all trading math to existing primitives; `paper == backtest` equality proven. (`d46cae5` → merge `f0ecf97`; 107 → **113** tests)
- **Typed loadable `StrategyRegistry`** — additive seam wrapping the builtin strategy dict, `registry == dict` equivalence proven. (`d9ac862` → merge `5a19839`; 113 → **119** tests)
- **CLI `paper` subcommand + registry strategy resolution** wired into the real CLI (was dead code); registry-only strategies are now CLI-resolvable for both `backtest` and `paper`. (`219038f` → merge `ac537ff`; 119 → **123** tests)
- **Risk-adjusted metrics** — annualized `sharpe`, `cagr`, `annualized_volatility` in `report.metrics()`, all derived from the existing equity curve (stdlib `statistics`), surfaced in `run.json` + `report.md`; hand-computed test proves the real formula. (`8000432` → merge `ed6a1f1`; 123 → **126** tests)

**Current state:** `master` @ `ed6a1f1` — 126 passing tests, three CLI subcommands (`backtest`, `paper`, `import-csv`), one strategy (`sma_cross`).

## In progress

- _Nothing actively on `master`._ The `chore/kb-consolidation` branch (this docs pass) is the only open local work.

## Planned-next

These are the engine's stated direction (per the README pitch and the existing `Broker` ABC / event-driver seams), not yet built:

- **Live broker integration** — a `Broker` ABC seam already exists for paper; live trading via the optional `shioaji` dependency (declared in `pyproject.toml`'s `broker` extra) is the natural next step. **No live order path exists yet.**
- **More strategies** — only `sma_cross` ships today; the `StrategyRegistry` is built to load others.
- **More risk metrics** — Sortino / Calmar / max-drawdown-duration would extend the risk-adjusted set now that Sharpe/CAGR/vol exist.
- **Data sourcing beyond CSV/Parquet** — current providers are offline-only by design; a real market-data fetcher is future work.

## Non-goals (for now)

- Real-money/live trading is **out of scope** until the live broker path is built and reviewed.
- Runtime network access during backtests — backtests are intentionally **fully offline** from cached bar data.
