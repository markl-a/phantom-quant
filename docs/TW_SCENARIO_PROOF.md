# Taiwan Rule Reproducibility Scenario

This P3 scenario proves the public value of `phantom-quant` as an offline
Taiwan-stock research lab. It connects Taiwan stock market rule assumptions
with backtest/paper reproducibility in one deterministic local artifact bundle.

It is research tooling only. It is not investment advice, does not make
performance guarantees, and does not enable live broker execution.

## Command

```powershell
python -m phantom_quant.cli tw-scenario `
  --csv .\tests\fixtures\sample_2330_1d.csv `
  --symbol 2330 `
  --short 3 `
  --long 6 `
  --cash 1000000 `
  --out .\artifacts\tw-scenario
```

The command writes:

- `manifest.json`
- `tw-rules.json`
- `parity.json`
- `summary.md`

The bundle uses a local CSV fixture, never connects to a broker, never uses real
money, never fetches market data from the network, and never reads broker
credentials.

## Manifest

Schema version 1:

```json
{
  "schema_version": 1,
  "mode": "taiwan_rule_reproducibility_scenario",
  "data_source": "csv_fixture",
  "broker": "disabled",
  "live_broker_execution": false,
  "real_money": false,
  "investment_advice": false,
  "external_network": false,
  "artifacts": [
    "manifest.json",
    "tw-rules.json",
    "parity.json",
    "summary.md"
  ]
}
```

## Taiwan Rules Artifact

`tw-rules.json` records a deterministic snapshot of the local Taiwan-stock
assumptions used by the engine:

```json
{
  "schema_version": 1,
  "mode": "taiwan_stock_rule_snapshot",
  "rule_scope": "offline_research_fixture",
  "investment_advice": false,
  "fee_model": {
    "fee_rate": "0.001425",
    "tax_rate": "0.003",
    "minimum_fee": "20",
    "lot_size": 1000
  },
  "tick_size_examples": [
    {"price": "9.99", "tick_size": "0.01"},
    {"price": "10", "tick_size": "0.05"},
    {"price": "50", "tick_size": "0.1"},
    {"price": "100", "tick_size": "0.5"},
    {"price": "500", "tick_size": "1"},
    {"price": "1000", "tick_size": "5"}
  ],
  "cost_examples": {
    "buy_2330_1000_at_600": "855",
    "sell_2330_1000_at_600": "2655"
  },
  "limit_band_example": {
    "prev_close": "100",
    "floor": "90.0",
    "ceiling": "110.0"
  },
  "limit_lock_examples": {
    "limit_up_buy_blocked": "buy blocked: locked limit-up, no sellers",
    "limit_down_sell_blocked": "sell blocked: locked limit-down, no buyers"
  }
}
```

## Parity Artifact

`parity.json` compares an offline backtest and simulated paper run using the
same fixture, strategy, parameters, cost model, and caller-supplied
reproducibility stamps:

```json
{
  "schema_version": 1,
  "mode": "backtest_paper_reproducibility_parity",
  "symbol": "2330",
  "strategy": "sma_cross",
  "broker": "disabled",
  "live_broker_execution": false,
  "real_money": false,
  "investment_advice": false,
  "data_source": "csv_fixture",
  "reproducibility": {
    "symbol": "2330",
    "strategy": "sma_cross",
    "timeframe": "1d",
    "start": "0000-00-00",
    "end": "9999-99-99",
    "cash": "1000000",
    "params": {
      "short": 3,
      "long": 6,
      "qty": 1000
    },
    "cost_model": "tw_stock",
    "bar_count": 25,
    "git_sha": "DEMO",
    "version": "0.1.0a0",
    "generated_at": "2026-06-26T00:00:00Z",
    "data_source": "csv_fixture",
    "broker": "disabled"
  },
  "backtest": {
    "num_bars": 25,
    "num_trades": 2,
    "metrics": {
      "total_return": "0.0246",
      "max_drawdown": "0.0174",
      "num_trades": 2
    }
  },
  "paper": {
    "num_bars": 25,
    "num_trades": 2,
    "metrics": {
      "total_return": "0.0246",
      "max_drawdown": "0.0174",
      "num_trades": 2
    }
  },
  "parity": {
    "trades_match": true,
    "equity_match": true,
    "metrics_match": true,
    "run_meta_diff": ["mode"]
  },
  "disclaimer": "Offline research scenario only; not investment advice."
}
```

The parity artifact must not name a winning strategy or recommend a trade. It
exists so reviewers can verify the paper path uses the same semantics as the
backtest path.

## Safety Boundary

- Live broker execution is disabled.
- Real money and real account data are out of scope.
- Broker tokens, API keys, account ids, and credentials must not appear in the
  bundle.
- The scenario is deterministic and fixture-based.
- Outputs are research artifacts, not trading recommendations.
