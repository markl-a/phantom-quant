# Risk Metrics Contract

This document defines the P2 public contract for the offline risk-metric and
strategy-comparison demo. It is research tooling only. It is not investment
advice, does not make performance guarantees, and does not enable live broker
execution.

## Command

```powershell
python -m phantom_quant.cli risk-demo `
  --csv .\tests\fixtures\sample_2330_1d.csv `
  --symbol 2330 `
  --short 3 `
  --long 6 `
  --cash 1000000 `
  --out .\artifacts\risk-demo
```

The command writes a deterministic offline bundle:

- `manifest.json`
- `risk-metrics.json`
- `strategy-comparison.json`
- `summary.md`

The bundle uses a local CSV fixture, never connects to a broker, never uses real
money, and never reads broker credentials.

## Manifest

Schema version 1:

```json
{
  "schema_version": 1,
  "mode": "offline_risk_metric_demo",
  "data_source": "csv_fixture",
  "broker": "disabled",
  "live_broker_execution": false,
  "real_money": false,
  "investment_advice": false,
  "external_network": false,
  "artifacts": [
    "manifest.json",
    "risk-metrics.json",
    "strategy-comparison.json",
    "summary.md"
  ]
}
```

## Risk Metrics Artifact

`risk-metrics.json` records deterministic diagnostics for two offline scenarios:

- `baseline`: same fixture and strategy with no slippage.
- `slippage_10bps`: same fixture and strategy with 10 bps adverse slippage.

Schema version 1 includes this metrics contract:

```json
{
  "schema_version": 1,
  "mode": "offline_risk_metric_demo",
  "risk_metrics_contract": [
    "total_return",
    "max_drawdown",
    "annualized_volatility",
    "sharpe",
    "average_exposure",
    "max_exposure",
    "turnover"
  ],
  "runs": [
    {
      "scenario": "baseline",
      "symbol": "2330",
      "strategy": "sma_cross",
      "params": {
        "short": 3,
        "long": 6,
        "qty": 1000,
        "slippage_bps": 0.0
      },
      "broker": "disabled",
      "data_source": "csv_fixture",
      "investment_advice": false,
      "total_return": "0.0246",
      "max_drawdown": "0.0174",
      "annualized_volatility": 0.062981,
      "sharpe": 4.080945,
      "average_exposure": "0.1179",
      "max_exposure": "0.6090",
      "turnover": "1.2235",
      "num_trades": 2,
      "num_gated": 0,
      "num_rejected": 0
    }
  ]
}
```

Definitions:

- `total_return`: end equity divided by start equity minus 1.
- `max_drawdown`: largest peak-to-trough equity decline.
- `annualized_volatility`: population standard deviation of bar returns,
  annualized with 252 trading periods.
- `sharpe`: annualized excess-return Sharpe with zero risk-free rate by default.
- `average_exposure`: average absolute marked position notional divided by
  equity across bars.
- `max_exposure`: maximum absolute marked position notional divided by equity.
- `turnover`: filled trade notional divided by starting equity.

## Strategy Comparison Artifact

`strategy-comparison.json` is diagnostic only:

```json
{
  "schema_version": 1,
  "mode": "strategy_risk_comparison",
  "ranking_policy": "diagnostic_not_recommendation",
  "winner": null,
  "investment_advice": false,
  "disclaimer": "Offline diagnostic comparison only; not investment advice.",
  "compared_scenarios": [
    {
      "scenario": "baseline",
      "total_return": "0.0246",
      "max_drawdown": "0.0174",
      "turnover": "1.2235",
      "average_exposure": "0.1179"
    }
  ]
}
```

The comparison artifact must not name a winning strategy or recommend a trade.
It exists so a reviewer can compare risk assumptions across deterministic
offline runs.

## Safety Boundary

- Live broker execution is disabled.
- Real money and real account data are out of scope.
- Broker tokens, API keys, account ids, and credentials must not appear in the
  bundle.
- Strategy/risk comparisons must remain diagnostic and must not be presented as
  recommendations.
