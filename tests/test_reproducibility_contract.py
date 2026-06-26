from __future__ import annotations

import json
from pathlib import Path

from phantom_quant.cli import main

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_2330_1d.csv"


def _common_args() -> list[str]:
    return [
        "--csv", str(FIXTURE),
        "--strategy", "sma_cross",
        "--symbol", "2330",
        "--short", "3",
        "--long", "6",
        "--cash", "1000000",
        "--git-sha", "TEST_SHA",
        "--version", "TEST_VERSION",
        "--generated-at", "2026-06-26T00:00:00Z",
    ]


def test_paper_artifacts_match_backtest_for_same_offline_fixture(tmp_path):
    bt_dir = tmp_path / "backtest-artifacts"
    pp_dir = tmp_path / "paper-artifacts"
    bt_report = tmp_path / "backtest.md"
    pp_report = tmp_path / "paper.md"

    assert main(["backtest", *_common_args(), "--artifacts", str(bt_dir), "--out", str(bt_report)]) == 0
    assert main(["paper", *_common_args(), "--artifacts", str(pp_dir), "--out", str(pp_report)]) == 0

    for name in ("trades.csv", "equity.csv"):
        assert (pp_dir / name).read_bytes() == (bt_dir / name).read_bytes()

    payload = json.loads((pp_dir / "run.json").read_text(encoding="utf-8"))
    bt_payload = json.loads((bt_dir / "run.json").read_text(encoding="utf-8"))
    assert payload["metrics"] == bt_payload["metrics"]
    assert payload["num_bars"] == bt_payload["num_bars"]
    assert payload["meta"]["mode"] == "paper"
    assert payload["meta"]["symbol"] == "2330"
    assert payload["meta"]["data_source"] == "csv_fixture"
    assert payload["meta"]["broker"] == "disabled"
    assert payload["meta"]["git_sha"] == "TEST_SHA"
    assert payload["meta"]["generated_at"] == "2026-06-26T00:00:00Z"


def test_run_json_records_reproducibility_inputs(tmp_path):
    out_dir = tmp_path / "artifacts"
    out_md = tmp_path / "report.md"

    assert main(["backtest", *_common_args(), "--artifacts", str(out_dir), "--out", str(out_md)]) == 0

    payload = json.loads((out_dir / "run.json").read_text(encoding="utf-8"))
    meta = payload["meta"]
    assert meta["mode"] == "backtest"
    assert meta["schema_version"] == 1
    assert meta["data_source"] == "csv_fixture"
    assert meta["broker"] == "disabled"
    assert meta["timeframe"] == "1d"
    assert meta["start"] == "0000-00-00"
    assert meta["end"] == "9999-99-99"
    assert meta["cash"] == "1000000"
    assert meta["params"] == {
        "long": 6,
        "qty": 1000,
        "short": 3,
        "slippage_bps": 0.0,
    }
