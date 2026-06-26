from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_readme_declares_research_only_and_default_off_broker_path():
    text = _read("README.md")
    low = text.lower()

    assert "Research-only" in text
    assert "not investment advice" in low
    assert "live broker execution" in low
    assert "disabled by default" in low
    assert "docs/PUBLIC_DEMO.md" in text
    assert "docs/REPRODUCIBILITY_CONTRACT.md" in text
    assert "docs/RISK_METRICS_CONTRACT.md" in text
    assert "docs/TW_SCENARIO_PROOF.md" in text
    assert "--generated-at" in text
    assert "risk-demo" in text
    assert "tw-scenario" in text


def test_public_demo_uses_offline_fixture_and_auditable_artifacts():
    text = _read("docs/PUBLIC_DEMO.md")
    low = text.lower()

    assert "tests\\fixtures\\sample_2330_1d.csv" in text
    assert "backtest" in low
    assert "paper" in low
    assert "trades.csv" in text
    assert "equity.csv" in text
    assert "run.json" in text
    assert "risk-metrics.json" in text
    assert "strategy-comparison.json" in text
    assert "tw-rules.json" in text
    assert "parity.json" in text
    assert "no broker" in low
    assert "real money" in low
    assert "diagnostic only" in low
    assert "live_broker_execution=false" in text


def test_reproducibility_contract_documents_backtest_and_paper_artifacts():
    text = _read("docs/REPRODUCIBILITY_CONTRACT.md")
    low = text.lower()

    assert "run.json" in text
    assert "trades.csv" in text
    assert "equity.csv" in text
    assert "paper --artifacts" in text
    assert "backtest --artifacts" in text
    assert "schema_version" in text
    assert "broker" in text
    assert "disabled" in low
    assert "not investment advice" in low


def test_risk_metrics_contract_documents_public_schema():
    text = _read("docs/RISK_METRICS_CONTRACT.md")
    low = text.lower()

    assert "risk-demo" in text
    assert "manifest.json" in text
    assert "risk-metrics.json" in text
    assert "strategy-comparison.json" in text
    assert '"schema_version": 1' in text
    assert '"broker": "disabled"' in text
    assert '"live_broker_execution": false' in text
    assert '"real_money": false' in text
    assert '"investment_advice": false' in text
    assert '"external_network": false' in text
    assert "average_exposure" in text
    assert "max_exposure" in text
    assert "turnover" in text
    assert '"params"' in text
    assert '"slippage_bps": 0.0' in text
    assert '"compared_scenarios"' in text
    assert "diagnostic_not_recommendation" in text
    assert "not investment advice" in low


def test_tw_scenario_proof_documents_p3_schema():
    text = _read("docs/TW_SCENARIO_PROOF.md")
    low = text.lower()

    assert "tw-scenario" in text
    assert "manifest.json" in text
    assert "tw-rules.json" in text
    assert "parity.json" in text
    assert '"schema_version": 1' in text
    assert '"mode": "taiwan_rule_reproducibility_scenario"' in text
    assert '"broker": "disabled"' in text
    assert '"live_broker_execution": false' in text
    assert '"real_money": false' in text
    assert '"investment_advice": false' in text
    assert '"external_network": false' in text
    assert '"fee_rate": "0.001425"' in text
    assert '"tax_rate": "0.003"' in text
    assert '"limit_band_example"' in text
    assert '"backtest"' in text
    assert '"paper"' in text
    assert '"params"' in text
    assert '"cost_model": "tw_stock"' in text
    assert '"trades_match": true' in text
    assert '"equity_match": true' in text
    assert '"metrics_match": true' in text
    assert "not investment advice" in low
