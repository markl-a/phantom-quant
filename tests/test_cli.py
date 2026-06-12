from pathlib import Path

from phantom_quant.cli import main

FIX = Path(__file__).parent / "fixtures" / "sample_2330_1d.csv"


def test_backtest_subcommand_writes_report(tmp_path, capsys):
    out = tmp_path / "report.md"
    rc = main(["backtest", "--csv", str(FIX), "--strategy", "sma_cross",
               "--symbol", "2330", "--cash", "1000000", "--out", str(out)])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "# phantom-quant backtest" in text and "2330" in text
    assert "report written" in capsys.readouterr().out


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
