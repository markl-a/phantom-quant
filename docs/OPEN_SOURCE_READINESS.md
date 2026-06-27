# Open Source Readiness

Project: `phantom-quant`
Current phase: P3 Taiwan-rule/reproducibility scenario proof slice verified
Master plan: `../../PHANTOM-SATELLITES-OPEN-SOURCE-MASTER-PLAN.md`

## Shipped Features

- Local Taiwan-stock research CLI for offline backtest, paper simulation, and CSV import.
- CLI entrypoint: `phantom-quant = phantom_quant.cli:main`.
- Help surface verified with `python -m phantom_quant.cli --help`.
- Subcommands include `backtest`, `paper`, and `import-csv`.
- Root README points to `docs/phantom-quant.md`.
- Root README now includes a research-only offline demo and no-advice/default-off live broker statement.
- Public demo/risk policy is documented in `docs/PUBLIC_DEMO.md`.
- Reproducibility artifact schema and backtest/paper parity contract are documented in `docs/REPRODUCIBILITY_CONTRACT.md`.
- CI skeleton is present at `.github/workflows/ci.yml` and runs the Python test suite.
- `paper --artifacts` writes the same artifact set as `backtest --artifacts`.
- Offline risk metrics and diagnostic comparison schemas are documented in `docs/RISK_METRICS_CONTRACT.md`.
- CLI supports `risk-demo --out` for deterministic offline risk metric and strategy comparison bundles.
- Risk demo bundles include `manifest.json`, `risk-metrics.json`, `strategy-comparison.json`, and `summary.md`; they record `broker=disabled`, `live_broker_execution=false`, `real_money=false`, `investment_advice=false`, and `external_network=false`.
- P3 Taiwan-rule and backtest/paper reproducibility scenario proof is documented in `docs/TW_SCENARIO_PROOF.md`.
- CLI supports `tw-scenario --out` for deterministic Taiwan-rule and reproducibility scenario bundles.
- TW scenario bundles include `manifest.json`, `tw-rules.json`, `parity.json`, and `summary.md`; they record Taiwan fee/tax/tick/limit-lock rule snapshots, backtest/paper parity, `broker=disabled`, `live_broker_execution=false`, `real_money=false`, `investment_advice=false`, and `external_network=false`.
- Test suite baseline after TW scenario additions: `python -m pytest -q` passed with 138 tests.

## Planned Or Deferred Features

- Broader local quant research lab: strategy plugin contract hardening, portfolio accounting, walk-forward testing, and more scenario variants.
- Live broker execution and real-time market data remain deferred and must be disabled by default.

## Install And Test Commands

```powershell
python -m pip install -e .[test]
python -m pytest -q
python -m phantom_quant.cli --help
python -m phantom_quant.cli backtest --csv .\tests\fixtures\sample_2330_1d.csv --strategy sma_cross --symbol 2330 --short 3 --long 6 --cash 1000000 --artifacts <temp>\artifacts --out <temp>\backtest.md
python -m phantom_quant.cli paper --csv .\tests\fixtures\sample_2330_1d.csv --strategy sma_cross --symbol 2330 --short 3 --long 6 --cash 1000000 --artifacts <temp>\paper-artifacts --out <temp>\paper.md
python -m phantom_quant.cli risk-demo --csv .\tests\fixtures\sample_2330_1d.csv --symbol 2330 --short 3 --long 6 --cash 1000000 --out <temp>\risk-demo
python -m phantom_quant.cli tw-scenario --csv .\tests\fixtures\sample_2330_1d.csv --symbol 2330 --short 3 --long 6 --cash 1000000 --out <temp>\tw-scenario
```

Observed result on 2026-06-26:

```text
python -m pytest tests/test_reproducibility_contract.py tests/test_open_source_contract.py tests/test_artifacts.py tests/test_cli.py tests/test_paper_cli_e2e.py tests/test_paper.py -q: 34 passed
python -m pytest tests/test_risk_demo_contract.py tests/test_open_source_contract.py tests/test_reproducibility_contract.py tests/test_artifacts.py tests/test_cli.py tests/test_paper_cli_e2e.py tests/test_paper.py tests/test_report.py -q: 48 passed
python -m pytest tests/test_tw_scenario_contract.py -q: 3 passed
python -m pytest tests/test_tw_scenario_contract.py tests/test_risk_demo_contract.py tests/test_open_source_contract.py tests/test_reproducibility_contract.py tests/test_artifacts.py tests/test_cli.py tests/test_paper_cli_e2e.py tests/test_paper.py tests/test_report.py -q: 52 passed
python -m pytest -q: 139 passed
python -m pytest --collect-only -q: 139 tests collected
```

## Fixture And Data Policy

- Public demos must use offline, reproducible market-data fixtures.
- No real account data, API keys, broker credentials, or private trading records may be committed.
- Result artifacts record schema version, mode, strategy params, caller-supplied stamps, data source, and `broker=disabled`.
- Risk metric artifacts must remain diagnostic-only, must not name a winning strategy, and must not present a trade recommendation.
- TW scenario artifacts must remain fixture-only and must not include broker credentials, account ids, API keys, live market data, or trade recommendations.

## Safety And Privacy Risks

- Users may misread backtest output as investment advice; docs must state research-only/no-advice.
- Live broker support, if present later, requires explicit governance and cannot be default.
- Strategy examples must avoid performance guarantees.

## Blockers To Next Phase

- None for the current P3 Taiwan-rule/reproducibility scenario proof slice.
- Remaining P3 work before Beta sign-off: strategy plugin contract hardening or walk-forward scenario variants without touching live execution.

## Evidence

- `pyproject.toml` declares package `phantom-quant` and script `phantom-quant`.
- `README.md` points to `docs/phantom-quant.md`.
- `README.md` states research-only, not investment advice, and live broker execution disabled by default.
- `docs/PUBLIC_DEMO.md` documents offline fixture demos, auditable artifacts, and no broker/no real money requirement.
- `docs/REPRODUCIBILITY_CONTRACT.md` documents `trades.csv`, `equity.csv`, `run.json`, `report.md`, schema version 1, `broker=disabled`, and backtest/paper parity expectations.
- `docs/RISK_METRICS_CONTRACT.md` documents `risk-demo`, `manifest.json`, `risk-metrics.json`, `strategy-comparison.json`, exposure/turnover fields, diagnostic comparison policy, and no-advice/no-broker boundary.
- `docs/TW_SCENARIO_PROOF.md` documents `tw-scenario`, `manifest.json`, `tw-rules.json`, `parity.json`, Taiwan fee/tax/tick/limit-lock examples, backtest/paper parity, reproducibility stamps, and no-advice/no-broker boundary.
- `.github/workflows/ci.yml` installs `.[test]` and runs `python -m pytest -q`.
- `python -m pytest tests/test_reproducibility_contract.py tests/test_open_source_contract.py -q`: 5 passed.
- `python -m pytest tests/test_reproducibility_contract.py tests/test_open_source_contract.py tests/test_artifacts.py tests/test_cli.py tests/test_paper_cli_e2e.py tests/test_paper.py -q`: 34 passed.
- `python -m pytest tests/test_risk_demo_contract.py tests/test_open_source_contract.py tests/test_reproducibility_contract.py tests/test_artifacts.py tests/test_cli.py tests/test_paper_cli_e2e.py tests/test_paper.py tests/test_report.py -q`: 48 passed.
- `python -m pytest tests/test_tw_scenario_contract.py -q`: 3 passed.
- `python -m pytest tests/test_tw_scenario_contract.py tests/test_risk_demo_contract.py tests/test_open_source_contract.py tests/test_reproducibility_contract.py tests/test_artifacts.py tests/test_cli.py tests/test_paper_cli_e2e.py tests/test_paper.py tests/test_report.py -q`: 52 passed.
- `python -m pytest -q`: 139 passed.
- `python -m pytest --collect-only -q`: 139 tests collected.
- `python -m phantom_quant.cli --help`: help OK.
- Isolated smoke:
  - `backtest` with `tests\fixtures\sample_2330_1d.csv`, `sma_cross`, `--short 3 --long 6`, `--artifacts <temp>\backtest-artifacts`: wrote `backtest.md`, `trades.csv`, `equity.csv`, `run.json`, and artifact `report.md`.
  - `paper` with the same fixture and params plus `--artifacts <temp>\paper-artifacts`: wrote `paper.md`, `trades.csv`, `equity.csv`, `run.json`, and artifact `report.md`.
  - backtest/paper `trades.csv` and `equity.csv` hashes matched; `run.json` recorded `mode=backtest`/`mode=paper`, `broker=disabled`, `schema_version=1`, `num_bars=25`.
- Risk smoke:
  - `risk-demo` with `tests\fixtures\sample_2330_1d.csv`, `sma_cross`, `--short 3 --long 6`, `--out <temp>\risk-demo`: wrote schema version 1 `manifest.json`, `risk-metrics.json`, `strategy-comparison.json`, and `summary.md`.
  - `manifest.json` recorded `broker=disabled`, `live_broker_execution=false`, `real_money=false`, `investment_advice=false`, and `external_network=false`.
  - `risk-metrics.json` recorded `average_exposure`, `max_exposure`, and `turnover` for baseline and `slippage_10bps`; `strategy-comparison.json` recorded `winner=null` and `ranking_policy=diagnostic_not_recommendation`.
- TW scenario smoke:
  - `tw-scenario` with `tests\fixtures\sample_2330_1d.csv`, `sma_cross`, `--short 3 --long 6`, `--out <temp>\tw-scenario`: wrote schema version 1 `manifest.json`, `tw-rules.json`, `parity.json`, and `summary.md`.
  - `manifest.json` recorded `broker=disabled`, `live_broker_execution=false`, `real_money=false`, `investment_advice=false`, and `external_network=false`.
  - `tw-rules.json` recorded Taiwan fee rate `0.001425`, tax rate `0.003`, tick-size examples, buy/sell cost examples, and limit-lock blocked reasons.
  - `parity.json` recorded backtest/paper `trades_match=true`, `equity_match=true`, `metrics_match=true`, and reproducibility stamps `git_sha=DEMO`, `version=0.1.0a0`, `generated_at=2026-06-26T00:00:00Z`.
- `agy` reviewer result: pass with one low-severity doc drift. `docs/REPRODUCIBILITY_CONTRACT.md` was corrected so the example `params` matches the implemented schema.
- `agy` P2 risk metrics reviewer result: no blockers for live broker/credential implication, investment-advice or performance-guarantee drift, strategy-comparison recommendation drift, nondeterminism, missing safety flags, exposure/turnover private-data or future-data issues, docs/tests mismatch, CLI/help mismatch, or backtest/paper artifact privacy regression.
- `agy` P3 TW scenario reviewer result: initial doc-code schema drift in `docs/TW_SCENARIO_PROOF.md` and `docs/RISK_METRICS_CONTRACT.md` was fixed; re-review found `NO BLOCKERS` for live broker/credential implication, investment-advice drift, external network use, determinism, honest backtest/paper parity, or risk-demo/backtest/paper regression.

## P4 Release-Prep Slice 1

Status: governance baseline added; this does not mark the project release-ready.

Evidence:
- `CONTRIBUTING.md` defines the contribution workflow, required test command, readiness-doc update rule, and no-private-data/no-credentials boundary.
- `SECURITY.md` defines private vulnerability reporting, supported version scope, 7-day acknowledgement target, and safe report contents.
- `python -m pytest tests/test_release_prep_contract.py -q`: 1 passed.
- `python -m pytest -q`: 140 passed.

Remaining P4 work: full release gate, final docs audit, package metadata audit, release notes, tag plan, and maintainer sign-off.

## P4 Release-Prep Slice 2

Status: final release gate checklist added; this does not mark the project release-ready.

Evidence:
- `CHANGELOG.md` records the unreleased governance/release-checklist work and points back to readiness evidence.
- `docs/RELEASE_CHECKLIST.md` documents final tests, dependency/license review, secret/private-data scan, known limitations, and manual maintainer approval.
- `python -m pytest tests/test_release_prep_contract.py -q`: 2 passed.
- `python -m pytest -q`: 141 passed.

Remaining P4 work: execute final scans, complete dependency/license review, finalize release notes, and record manual maintainer approval.

## P4 Release-Prep Slice 3

Status: final scan and direct dependency/license audit recorded; not release-ready.

Evidence:
- `docs/FINAL_RELEASE_AUDIT.md` records scan scope, `high_conf_secret_hits=0`, direct dependency/license review, and remaining release blockers.
- Direct release-scope dependency metadata reviewed: `pandas==3.0.3` BSD 3-Clause, `numpy==2.4.6` permissive BSD/MIT/Zlib/0BSD/CC0 expression, `pyarrow==24.0.0` Apache-2.0.
- Optional broker dependency remains outside the default offline release path and requires separate live-trading approval.
- `python -m pytest tests/test_release_prep_contract.py -q`: 3 passed.
- `python -m pytest -q`: 142 passed.

Remaining P4 work: release notes finalization, tag plan, final maintainer approval, and separate optional broker review before any live path is supported.

## P4 Release-Prep Slice 4

Status: maintainer approval recorded, conductor sign-off complete, and release-candidate tag created.

Evidence:
- `docs/RELEASE_NOTES.md` records public release-candidate notes, known limitations, and verification pointers.
- `docs/TAG_PLAN.md` records proposed tag `v0.1.0-alpha.0`, required approval-before-tag sequence, and rollback steps.
- `docs/PUBLIC_RELEASE_APPROVAL.md` records `Status: approved` with approver, approval date, and approved tag.
- Conductor root approval packet `PHANTOM-SATELLITES-PUBLIC-RELEASE-APPROVAL.md` records all ten candidate tags as approved.
- `.github/workflows/ci.yml` runs an explicit `release-prep gate` against `tests/test_release_prep_contract.py`.
- `python -m pytest tests/test_release_prep_contract.py -q`: 5 passed.
- `python -m pytest -q`: 144 passed.

Remaining P4 work: none for the approved release-candidate tag.

## P4 Release-Prep Slice 5

Status: current release-candidate verification refreshed for package metadata, CI, wheel, lint, deterministic public smoke, and secret scan.

Evidence:
- `pyproject.toml` declares Apache-2.0 metadata, author metadata, Python classifiers, project URLs, and `test`/`dev` extras.
- `.github/workflows/ci.yml` installs `.[dev]`, builds a wheel, runs `ruff`, runs the full test suite, runs deterministic public smoke commands, and runs the release-prep gate.
- `tests/test_packaging.py` verifies package metadata, default dependency surface, optional broker extra, and the `phantom-quant` CLI entrypoint target.
- `tests/test_release_prep_contract.py` verifies CI release gates and current audit evidence.
- `python -m pip install -e . --dry-run --no-deps`: passed; would install `phantom-quant-0.1.0a0`.
- `python -m pip wheel . --no-deps -w <temp>`: passed; built `phantom_quant-0.1.0a0-py3-none-any.whl`.
- `python -m phantom_quant.cli --help`: passed.
- Deterministic public smoke path: passed for `backtest`, `paper`, `risk-demo`, and `tw-scenario`; manifests and run metadata record offline/no-broker/no-real-money/no-advice/no-network boundaries.
- `python -m ruff check .`: passed; all checks passed.
- `python -m pytest -q`: passed; 147 tests passed.
- Root `python .\run_phantom_satellite_usage_smoke.py`: passed; 10/10 projects OK.
- Root `python .\run_phantom_agent_compat_smoke.py`: passed; 40/40 invocations OK.
- Root `python -m pytest .\tests -q`: passed; 85 tests passed.
- High-confidence secret scan: `high_conf_secret_hits=0`.

Remaining P4 work: none for this public source release candidate.
