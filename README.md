# phantom-quant

> 台股 backtest → paper → live 交易引擎（phantom-mesh 生態系)。離線回測,可稽核、可重現的數字 —— 無券商、無真實金錢。

## Quickstart

```powershell
python -m pip install -e .[test]
python -m pytest -q
python -m phantom_quant.cli --help
```

Research-only offline demo:

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

Research-only: this is not investment advice and does not make performance
guarantees. Live broker execution is disabled by default and is not part of the
public demo; see [docs/PUBLIC_DEMO.md](docs/PUBLIC_DEMO.md).
Stable artifact schemas and reproducibility assumptions are documented in
[docs/REPRODUCIBILITY_CONTRACT.md](docs/REPRODUCIBILITY_CONTRACT.md).
Offline risk metrics and diagnostic strategy comparison artifacts are
documented in [docs/RISK_METRICS_CONTRACT.md](docs/RISK_METRICS_CONTRACT.md).
The P3 Taiwan-rule and backtest/paper reproducibility scenario proof is
documented in [docs/TW_SCENARIO_PROOF.md](docs/TW_SCENARIO_PROOF.md).

📄 完整文件(狀態/路線圖/方向):見 [docs/phantom-quant.md](docs/phantom-quant.md)
