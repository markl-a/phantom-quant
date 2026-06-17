"""P1-3 — auditable result artifacts: deterministic, byte-stable on-disk export.

A backtest must be able to write its trade tape, equity curve, and run metadata
to disk as byte-stable files so a run is reproducible and adversarially auditable.
The golden test pins the bytes of a fixed backtest; regenerate intentionally with
``PHANTOM_QUANT_UPDATE_GOLDEN=1 pytest tests/test_artifacts.py``.
"""
import json
import os
from decimal import Decimal
from pathlib import Path

import pytest

from phantom_quant import costs
from phantom_quant.artifacts import RunMeta, write_artifacts
from phantom_quant.backtest.engine import run_backtest
from phantom_quant.data.provider import CsvProvider
from phantom_quant.strategies.sma_cross import SmaCross


def _build_result_and_meta():
    fixture_csv = Path(__file__).parent / "fixtures" / "sample_2330_1d.csv"
    bars = CsvProvider(str(fixture_csv)).get_bars(
        "2330", "1d", "0000-00-00", "9999-99-99"
    )
    result = run_backtest(
        bars,
        SmaCross(short=3, long=6, qty=1000),
        cash=Decimal("1000000"),
        cost_fn=costs.trade_cost,
    )
    meta = RunMeta(
        symbol="2330",
        strategy="sma_cross",
        params={"short": 3, "long": 6, "qty": 1000},
        cash="1000000",
        bar_count=len(bars),
        git_sha="GOLDEN_SHA",
        version="GOLDEN_VER",
        generated_at="2026-01-01T00:00:00Z",
    )
    return result, meta


def test_write_artifacts_returns_all_paths(tmp_path):
    result, meta = _build_result_and_meta()

    paths = write_artifacts(result, meta, tmp_path)

    assert set(paths) == {"trades", "equity", "run", "report"}
    assert all(path.exists() for path in paths.values())


def test_artifacts_are_byte_stable_across_two_writes(tmp_path):
    result_a, meta_a = _build_result_and_meta()
    result_b, meta_b = _build_result_and_meta()

    paths_a = write_artifacts(result_a, meta_a, tmp_path / "a")
    paths_b = write_artifacts(result_b, meta_b, tmp_path / "b")

    for key in ("trades", "equity", "run"):
        assert paths_a[key].read_bytes() == paths_b[key].read_bytes()


def test_no_crlf_in_csv(tmp_path):
    result, meta = _build_result_and_meta()

    paths = write_artifacts(result, meta, tmp_path)

    assert b"\r\n" not in paths["trades"].read_bytes()
    assert b"\r\n" not in paths["equity"].read_bytes()


def test_trades_csv_header(tmp_path):
    result, meta = _build_result_and_meta()

    paths = write_artifacts(result, meta, tmp_path)

    first_line = paths["trades"].read_text(encoding="utf-8").splitlines()[0]
    assert first_line == "ts,symbol,side,qty,price,cost,status,reason"


def test_equity_csv_header(tmp_path):
    result, meta = _build_result_and_meta()

    paths = write_artifacts(result, meta, tmp_path)

    first_line = paths["equity"].read_text(encoding="utf-8").splitlines()[0]
    assert first_line == "ts,equity"


def test_run_json_has_meta_and_metrics(tmp_path):
    result, meta = _build_result_and_meta()

    paths = write_artifacts(result, meta, tmp_path)
    payload = json.loads(paths["run"].read_text(encoding="utf-8"))

    assert {"meta", "metrics", "num_bars"} <= set(payload)
    assert payload["meta"]["git_sha"] == "GOLDEN_SHA"
    assert payload["meta"]["generated_at"] == "2026-01-01T00:00:00Z"
    assert "total_return" in payload["metrics"]


def test_decimal_strategy_params_do_not_crash_json(tmp_path):
    # Regression: params may carry Decimal values (money/rates/thresholds are
    # Decimal end-to-end). write_artifacts must sanitize the WHOLE payload, not
    # only metrics, or json.dumps raises "Object of type Decimal is not JSON
    # serializable".
    result, _ = _build_result_and_meta()
    meta = RunMeta(
        symbol="2330", strategy="sma_cross",
        params={"threshold": Decimal("0.05"), "qty": 1000},
        cash="1000000", git_sha="X", version="Y", generated_at="Z",
    )
    paths = write_artifacts(result, meta, tmp_path)
    payload = json.loads(paths["run"].read_text(encoding="utf-8"))
    # Decimal serialized as its string form
    assert payload["meta"]["params"]["threshold"] == "0.05"


def test_golden_artifacts(tmp_path):
    result, meta = _build_result_and_meta()
    paths = write_artifacts(result, meta, tmp_path)

    golden_dir = Path(__file__).parent / "golden" / "sample_2330_sma36"
    artifact_names = ("trades.csv", "equity.csv", "run.json")

    if os.getenv("PHANTOM_QUANT_UPDATE_GOLDEN"):
        golden_dir.mkdir(parents=True, exist_ok=True)
        for name in artifact_names:
            key = Path(name).stem
            (golden_dir / name).write_bytes(paths[key].read_bytes())
        return

    for name in artifact_names:
        golden_path = golden_dir / name
        if not golden_path.exists():
            pytest.fail(
                f"Missing golden file {golden_path}. "
                "Run with PHANTOM_QUANT_UPDATE_GOLDEN=1 to generate it."
            )

        key = Path(name).stem
        assert paths[key].read_bytes() == golden_path.read_bytes()
