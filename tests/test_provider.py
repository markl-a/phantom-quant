from pathlib import Path

from phantom_quant.bars import Bar
from phantom_quant.data.provider import CsvProvider

FIX = Path(__file__).parent / "fixtures" / "sample_2330_1d.csv"


def test_csv_provider_returns_bars_in_range():
    bars = CsvProvider(FIX).get_bars("2330", "1d", "2026-05-01", "2026-06-05")
    assert len(bars) == 25
    assert isinstance(bars[0], Bar)
    assert bars[0].ts == "2026-05-01" and bars[0].close == 900.0
    assert bars[-1].ts == "2026-06-05"


def test_csv_provider_filters_by_date_and_symbol():
    bars = CsvProvider(FIX).get_bars("2330", "1d", "2026-05-09", "2026-05-12")
    assert [b.ts for b in bars] == ["2026-05-09", "2026-05-12"]
    assert CsvProvider(FIX).get_bars("9999", "1d", "2026-05-01", "2026-06-05") == []
