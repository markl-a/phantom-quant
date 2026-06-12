from phantom_quant.bars import Bar
from phantom_quant.data import store


def test_save_then_load_roundtrips_bars(tmp_path):
    bars = [
        Bar("2026-05-01", "2330", 900, 905, 898, 900, 20000),
        Bar("2026-05-02", "2330", 900, 902, 896, 899, 18000),
    ]
    p = tmp_path / "2330_1d.parquet"
    store.save_bars(bars, p)
    loaded = store.load_bars(p)
    assert loaded == bars
