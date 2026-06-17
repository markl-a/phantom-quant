from pathlib import Path

from phantom_quant.cli import main
from phantom_quant.data import store

FIX = Path(__file__).parent / "fixtures" / "sample_2330_1d.csv"


def test_backtest_subcommand_writes_report(tmp_path, capsys):
    out = tmp_path / "report.md"
    rc = main(["backtest", "--csv", str(FIX), "--strategy", "sma_cross",
               "--symbol", "2330", "--cash", "1000000", "--out", str(out)])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "# phantom-quant backtest" in text and "2330" in text
    assert "report written" in capsys.readouterr().out


def test_backtest_artifacts_flag_writes_all_files(tmp_path, capsys):
    out = tmp_path / "report.md"
    artdir = tmp_path / "run"
    rc = main(["backtest", "--csv", str(FIX), "--strategy", "sma_cross",
               "--symbol", "2330", "--cash", "1000000",
               "--short", "3", "--long", "6",
               "--git-sha", "deadbeef", "--version", "9.9.9",
               "--artifacts", str(artdir), "--out", str(out)])
    assert rc == 0
    for name in ("trades.csv", "equity.csv", "run.json", "report.md"):
        assert (artdir / name).exists(), name
    import json
    payload = json.loads((artdir / "run.json").read_text(encoding="utf-8"))
    assert payload["meta"]["git_sha"] == "deadbeef"
    assert payload["meta"]["version"] == "9.9.9"
    assert payload["meta"]["params"] == {"short": 3, "long": 6, "qty": 1000}
    assert "artifacts written" in capsys.readouterr().out


def test_unknown_strategy_errors(tmp_path):
    rc = main(["backtest", "--csv", str(FIX), "--strategy", "nope",
               "--symbol", "2330", "--out", str(tmp_path / "r.md")])
    assert rc == 2


def test_short_long_params_produce_a_round_trip(tmp_path):
    # --short/--long override SmaCross defaults so the shipped demo actually trades
    out = tmp_path / "r.md"
    rc = main(["backtest", "--csv", str(FIX), "--strategy", "sma_cross",
               "--symbol", "2330", "--cash", "1000000",
               "--short", "3", "--long", "6", "--out", str(out)])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "trades: 2 (closed: 1)" in text  # one buy + one sell round-trip


def test_import_csv_loads_fixture_into_parquet_schema(tmp_path, capsys):
    out = tmp_path / "2330_1d.parquet"
    rc = main(["import-csv", "--csv", str(FIX), "--symbol", "2330", "--out", str(out)])
    assert rc == 0
    assert out.exists()
    # round-trips through the store into the expected Bar schema
    bars = store.load_bars(out)
    assert len(bars) == 25
    assert bars[0].ts == "2026-05-01" and bars[0].symbol == "2330"
    assert bars[0].close == 900.0
    assert "imported" in capsys.readouterr().out.lower()


def test_import_csv_filters_by_symbol(tmp_path):
    out = tmp_path / "only_2330.parquet"
    rc = main(["import-csv", "--csv", str(FIX), "--symbol", "2330", "--out", str(out)])
    assert rc == 0
    bars = store.load_bars(out)
    assert {b.symbol for b in bars} == {"2330"}


def test_import_csv_missing_symbol_errors(tmp_path):
    out = tmp_path / "empty.parquet"
    rc = main(["import-csv", "--csv", str(FIX), "--symbol", "9999", "--out", str(out)])
    assert rc == 2  # no rows for that symbol -> clear error, no empty parquet
    assert not out.exists()
