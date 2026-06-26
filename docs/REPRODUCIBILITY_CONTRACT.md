# Reproducibility Contract

`phantom-quant` P2 artifacts are research-only, offline, and deterministic.
They are not investment advice and do not make performance guarantees.

The public reproducibility path uses a checked-in CSV fixture, no broker, no
API key, no network fetch, and no real money.

## Commands

Backtest artifact bundle:

```powershell
python -m phantom_quant.cli backtest `
  --csv .\tests\fixtures\sample_2330_1d.csv `
  --strategy sma_cross --symbol 2330 --short 3 --long 6 --cash 1000000 `
  --git-sha TEST_SHA --version TEST_VERSION --generated-at 2026-06-26T00:00:00Z `
  --artifacts .\artifacts\backtest `
  --out .\artifacts\backtest.md
```

Paper artifact bundle:

```powershell
python -m phantom_quant.cli paper `
  --csv .\tests\fixtures\sample_2330_1d.csv `
  --strategy sma_cross --symbol 2330 --short 3 --long 6 --cash 1000000 `
  --git-sha TEST_SHA --version TEST_VERSION --generated-at 2026-06-26T00:00:00Z `
  --artifacts .\artifacts\paper `
  --out .\artifacts\paper.md
```

## Artifact Files

Both `backtest --artifacts` and `paper --artifacts` write:

- `trades.csv`: deterministic trade tape.
- `equity.csv`: deterministic equity curve.
- `run.json`: reproducibility metadata and metrics.
- `report.md`: human-readable research report.

CSV files use LF line endings for byte stability. `run.json` is written with
sorted keys and caller-supplied stamps so tests can pin stable bytes.

## run.json Schema

Schema version 1:

```json
{
  "meta": {
    "schema_version": 1,
    "mode": "backtest",
    "symbol": "2330",
    "strategy": "sma_cross",
    "timeframe": "1d",
    "start": "0000-00-00",
    "end": "9999-99-99",
    "cash": "1000000",
    "params": {
      "short": 3,
      "long": 6,
      "qty": 1000,
      "slippage_bps": 0.0
    },
    "cost_model": "tw_stock",
    "bar_count": 10,
    "data_source": "csv_fixture",
    "broker": "disabled",
    "git_sha": "TEST_SHA",
    "version": "TEST_VERSION",
    "generated_at": "2026-06-26T00:00:00Z"
  },
  "metrics": {},
  "num_bars": 10
}
```

`mode` is either `backtest` or `paper`. For the same offline fixture and the
same deterministic strategy parameters, `paper` and `backtest` should produce
the same `trades.csv`, `equity.csv`, metrics, and `num_bars`; `run.json` differs
only where metadata must truthfully identify the run mode.

## Boundaries

- `broker` is `disabled` in public artifacts.
- Live broker execution is not part of this contract.
- Live market data is not part of this contract.
- Artifacts are research outputs, not trading recommendations.
