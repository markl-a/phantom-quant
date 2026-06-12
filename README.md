# phantom-quant

> 台股 backtest → paper → live trading engine for the phantom-mesh ecosystem. **v1 = P0: data + backtest only** (no orders, no real money).

Backtests run **fully offline** from cached bar data — no broker, no network. See the design spec (goal_plan/docs/34) and plan (goal_plan/docs/35).

## Quickstart (Windows / PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
$env:PYTHONUTF8="1"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\phantom-quant.exe backtest --csv tests\fixtures\sample_2330_1d.csv --strategy sma_cross --symbol 2330 --cash 1000000 --out report.md
```
