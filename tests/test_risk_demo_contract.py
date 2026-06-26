from __future__ import annotations

import json
from pathlib import Path

from phantom_quant import risk
from phantom_quant.cli import main

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_2330_1d.csv"


def test_risk_demo_bundle_writes_public_artifacts(tmp_path):
    out = tmp_path / "risk-demo"

    result = risk.write_risk_demo_bundle(
        csv_path=FIXTURE,
        out_dir=out,
        symbol="2330",
        short=3,
        long=6,
        cash="1000000",
    )

    assert result == out
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    metrics = json.loads((out / "risk-metrics.json").read_text(encoding="utf-8"))
    comparison = json.loads((out / "strategy-comparison.json").read_text(encoding="utf-8"))
    summary = (out / "summary.md").read_text(encoding="utf-8")

    assert manifest["schema_version"] == 1
    assert manifest["mode"] == "offline_risk_metric_demo"
    assert manifest["data_source"] == "csv_fixture"
    assert manifest["broker"] == "disabled"
    assert manifest["live_broker_execution"] is False
    assert manifest["real_money"] is False
    assert manifest["investment_advice"] is False
    assert manifest["external_network"] is False
    assert manifest["artifacts"] == [
        "manifest.json",
        "risk-metrics.json",
        "strategy-comparison.json",
        "summary.md",
    ]

    assert metrics["schema_version"] == 1
    assert metrics["risk_metrics_contract"] == [
        "total_return",
        "max_drawdown",
        "annualized_volatility",
        "sharpe",
        "average_exposure",
        "max_exposure",
        "turnover",
    ]
    assert [row["scenario"] for row in metrics["runs"]] == ["baseline", "slippage_10bps"]
    for row in metrics["runs"]:
        assert row["broker"] == "disabled"
        assert row["data_source"] == "csv_fixture"
        assert row["strategy"] == "sma_cross"
        assert "max_drawdown" in row
        assert "average_exposure" in row
        assert "turnover" in row
        assert row["investment_advice"] is False

    assert comparison["schema_version"] == 1
    assert comparison["winner"] is None
    assert comparison["ranking_policy"] == "diagnostic_not_recommendation"
    assert comparison["investment_advice"] is False
    assert "not investment advice" in comparison["disclaimer"].lower()

    bundle_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (out / "manifest.json", out / "risk-metrics.json", out / "strategy-comparison.json")
    )
    assert "api_key" not in bundle_text.lower()
    assert "broker_token" not in bundle_text.lower()
    assert "account_id" not in bundle_text.lower()
    assert "not investment advice" in summary.lower()


def test_risk_demo_bundle_is_deterministic(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"

    risk.write_risk_demo_bundle(FIXTURE, left, symbol="2330", short=3, long=6, cash="1000000")
    risk.write_risk_demo_bundle(FIXTURE, right, symbol="2330", short=3, long=6, cash="1000000")

    for name in ["manifest.json", "risk-metrics.json", "strategy-comparison.json", "summary.md"]:
        assert (left / name).read_text(encoding="utf-8") == (
            right / name
        ).read_text(encoding="utf-8")


def test_cli_risk_demo_writes_bundle(tmp_path, capsys):
    out = tmp_path / "cli-risk"

    rc = main([
        "risk-demo",
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
        "risk-metrics.json",
        "strategy-comparison.json",
        "summary.md",
    ]
    assert (out / "risk-metrics.json").exists()
