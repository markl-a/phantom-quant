from __future__ import annotations

import json
from pathlib import Path

from phantom_quant import tw_scenario
from phantom_quant.cli import main

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_2330_1d.csv"


def test_tw_scenario_bundle_proves_rules_and_reproducibility(tmp_path):
    out = tmp_path / "tw-scenario"

    result = tw_scenario.write_tw_scenario_bundle(
        csv_path=FIXTURE,
        out_dir=out,
        symbol="2330",
        short=3,
        long=6,
        cash="1000000",
    )

    assert result == out
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    rules = json.loads((out / "tw-rules.json").read_text(encoding="utf-8"))
    parity = json.loads((out / "parity.json").read_text(encoding="utf-8"))
    summary = (out / "summary.md").read_text(encoding="utf-8")

    assert manifest["schema_version"] == 1
    assert manifest["mode"] == "taiwan_rule_reproducibility_scenario"
    assert manifest["data_source"] == "csv_fixture"
    assert manifest["broker"] == "disabled"
    assert manifest["live_broker_execution"] is False
    assert manifest["real_money"] is False
    assert manifest["investment_advice"] is False
    assert manifest["external_network"] is False
    assert manifest["artifacts"] == [
        "manifest.json",
        "tw-rules.json",
        "parity.json",
        "summary.md",
    ]

    assert rules["schema_version"] == 1
    assert rules["mode"] == "taiwan_stock_rule_snapshot"
    assert rules["fee_model"]["fee_rate"] == "0.001425"
    assert rules["fee_model"]["tax_rate"] == "0.003"
    assert rules["fee_model"]["minimum_fee"] == "20"
    assert rules["tick_size_examples"] == [
        {"price": "9.99", "tick_size": "0.01"},
        {"price": "10", "tick_size": "0.05"},
        {"price": "50", "tick_size": "0.1"},
        {"price": "100", "tick_size": "0.5"},
        {"price": "500", "tick_size": "1"},
        {"price": "1000", "tick_size": "5"},
    ]
    assert rules["cost_examples"]["buy_2330_1000_at_600"] == "855"
    assert rules["cost_examples"]["sell_2330_1000_at_600"] == "2655"
    assert rules["limit_lock_examples"]["limit_up_buy_blocked"] == (
        "buy blocked: locked limit-up, no sellers"
    )
    assert rules["limit_lock_examples"]["limit_down_sell_blocked"] == (
        "sell blocked: locked limit-down, no buyers"
    )

    assert parity["schema_version"] == 1
    assert parity["mode"] == "backtest_paper_reproducibility_parity"
    assert parity["symbol"] == "2330"
    assert parity["strategy"] == "sma_cross"
    assert parity["broker"] == "disabled"
    assert parity["live_broker_execution"] is False
    assert parity["investment_advice"] is False
    assert parity["data_source"] == "csv_fixture"
    assert parity["backtest"]["num_bars"] == 25
    assert parity["paper"]["num_bars"] == 25
    assert parity["parity"]["trades_match"] is True
    assert parity["parity"]["equity_match"] is True
    assert parity["parity"]["metrics_match"] is True
    assert parity["parity"]["run_meta_diff"] == ["mode"]
    assert parity["reproducibility"]["git_sha"] == "DEMO"
    assert parity["reproducibility"]["version"] == "0.1.0a0"
    assert parity["reproducibility"]["generated_at"] == "2026-06-26T00:00:00Z"
    assert "not investment advice" in parity["disclaimer"].lower()
    assert "Taiwan" in summary

    bundle_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (out / "manifest.json", out / "tw-rules.json", out / "parity.json")
    )
    assert "api_key" not in bundle_text.lower()
    assert "broker_token" not in bundle_text.lower()
    assert "account_id" not in bundle_text.lower()


def test_tw_scenario_bundle_is_deterministic(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"

    tw_scenario.write_tw_scenario_bundle(
        csv_path=FIXTURE,
        out_dir=left,
        symbol="2330",
        short=3,
        long=6,
        cash="1000000",
    )
    tw_scenario.write_tw_scenario_bundle(
        csv_path=FIXTURE,
        out_dir=right,
        symbol="2330",
        short=3,
        long=6,
        cash="1000000",
    )

    for name in ["manifest.json", "tw-rules.json", "parity.json", "summary.md"]:
        assert (left / name).read_text(encoding="utf-8") == (
            right / name
        ).read_text(encoding="utf-8")


def test_cli_tw_scenario_writes_bundle(tmp_path, capsys):
    out = tmp_path / "cli-tw"

    rc = main([
        "tw-scenario",
        "--csv", str(FIXTURE),
        "--symbol", "2330",
        "--short", "3",
        "--long", "6",
        "--cash", "1000000",
        "--out", str(out),
    ])

    assert rc == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["out_dir"] == str(out)
    assert printed["artifacts"] == [
        "manifest.json",
        "tw-rules.json",
        "parity.json",
        "summary.md",
    ]
    assert (out / "parity.json").exists()
