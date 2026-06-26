# Public Demo Contract

`phantom-quant` public demos are research-only, offline, and deterministic. They
must not use broker credentials, live market data, or real money.

The current public surface is:

- `backtest`: run an offline backtest from a checked-in CSV fixture.
- `paper`: run simulated paper trading from the same checked-in CSV fixture.
- `import-csv`: convert a local CSV into the local Parquet cache schema.
- `tw-scenario`: write the P3 Taiwan-rule and backtest/paper reproducibility
  proof bundle.

Live broker execution is not part of the default public demo. The optional
`broker` extra exists for future work, but real broker support must remain
explicitly opt-in and governed before any release claim.

## Isolated Smoke Demo

```powershell
$root = Join-Path $env:TEMP ("phantom-quant-demo-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $root | Out-Null

python -m phantom_quant.cli backtest `
  --csv .\tests\fixtures\sample_2330_1d.csv `
  --strategy sma_cross --symbol 2330 --short 3 --long 6 --cash 1000000 `
  --git-sha DEMO --version 0.1.0a0 --generated-at 2026-06-26T00:00:00Z `
  --artifacts (Join-Path $root "artifacts") `
  --out (Join-Path $root "backtest.md")

python -m phantom_quant.cli paper `
  --csv .\tests\fixtures\sample_2330_1d.csv `
  --strategy sma_cross --symbol 2330 --short 3 --long 6 --cash 1000000 `
  --git-sha DEMO --version 0.1.0a0 --generated-at 2026-06-26T00:00:00Z `
  --artifacts (Join-Path $root "paper-artifacts") `
  --out (Join-Path $root "paper.md")

python -m phantom_quant.cli risk-demo `
  --csv .\tests\fixtures\sample_2330_1d.csv `
  --symbol 2330 --short 3 --long 6 --cash 1000000 `
  --out (Join-Path $root "risk-demo")

python -m phantom_quant.cli tw-scenario `
  --csv .\tests\fixtures\sample_2330_1d.csv `
  --symbol 2330 --short 3 --long 6 --cash 1000000 `
  --out (Join-Path $root "tw-scenario")

Remove-Item -LiteralPath $root -Recurse -Force
```

Expected shape:

- `backtest.md` and `paper.md` are written from the same offline fixture.
- `--artifacts` writes `trades.csv`, `equity.csv`, `run.json`, and `report.md`.
- `paper --artifacts` writes the same artifact set. With the same fixture and
  params, the paper run should match backtest trade/equity outputs and metrics.
- `risk-demo` writes `manifest.json`, `risk-metrics.json`,
  `strategy-comparison.json`, and `summary.md` from the same offline fixture.
- `tw-scenario` writes `manifest.json`, `tw-rules.json`, `parity.json`, and
  `summary.md`; it records `broker=disabled`, `live_broker_execution=false`,
  `real_money=false`, `investment_advice=false`, and
  `external_network=false`.
- No broker SDK, account, API key, network fetch, or real order is required.

## Risk Policy

- This is not investment advice and does not make performance guarantees.
- Backtest and paper outputs are research artifacts, not live trading
  recommendations.
- Strategy/risk comparisons are diagnostic only and must not name a winning
  strategy or recommend a trade.
- Real broker execution, if added later, requires explicit governance,
  approval gates, and a default-off kill switch.
