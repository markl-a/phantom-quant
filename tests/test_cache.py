"""P1-2 — data/cache workflow: CachedProvider + Parquet validation.

All hermetic/offline: a fake in-memory delegate provider stands in for any
live source, so nothing touches a market API or the network.
"""
from pathlib import Path

import pandas as pd
import pytest

from phantom_quant.bars import Bar
from phantom_quant.data.provider import BarProvider, CachedProvider
from phantom_quant.data import store


class _CountingProvider(BarProvider):
    """A delegate that records how many times get_bars was actually called."""

    def __init__(self, bars):
        self._bars = bars
        self.calls = 0

    def get_bars(self, symbol, timeframe, start, end):
        self.calls += 1
        return [b for b in self._bars
                if b.symbol == symbol and start <= b.ts <= end]


_BARS = [
    Bar("2026-05-01", "2330", 900.0, 905.0, 898.0, 900.0, 20000),
    Bar("2026-05-02", "2330", 900.0, 902.0, 896.0, 899.0, 18000),
    Bar("2026-05-05", "2330", 899.0, 901.0, 895.0, 898.0, 17000),
]


def test_cache_miss_fetches_then_hit_serves_without_refetch(tmp_path):
    delegate = _CountingProvider(_BARS)
    cp = CachedProvider(delegate, cache_dir=tmp_path)

    first = cp.get_bars("2330", "1d", "2026-05-01", "2026-05-05")
    assert delegate.calls == 1
    assert first == _BARS

    # second identical request: served from disk, delegate NOT called again
    second = cp.get_bars("2330", "1d", "2026-05-01", "2026-05-05")
    assert delegate.calls == 1            # no re-fetch
    assert second == first == _BARS       # byte-for-byte identical bars


def test_cache_writes_a_parquet_file(tmp_path):
    delegate = _CountingProvider(_BARS)
    cp = CachedProvider(delegate, cache_dir=tmp_path)
    cp.get_bars("2330", "1d", "2026-05-01", "2026-05-05")
    parquets = list(Path(tmp_path).rglob("*.parquet"))
    assert len(parquets) == 1


def test_different_key_does_not_collide(tmp_path):
    delegate = _CountingProvider(_BARS)
    cp = CachedProvider(delegate, cache_dir=tmp_path)
    cp.get_bars("2330", "1d", "2026-05-01", "2026-05-05")
    cp.get_bars("2330", "1d", "2026-05-01", "2026-05-02")   # different range -> new key
    assert delegate.calls == 2


# --- Parquet validation: corrupt / wrong-schema files are detected ----------

def test_corrupt_parquet_raises_clear_error(tmp_path):
    bad = tmp_path / "garbage.parquet"
    bad.write_bytes(b"this is not a parquet file at all")
    with pytest.raises(store.ParquetValidationError) as ei:
        store.load_bars(bad)
    assert str(bad) in str(ei.value) or "parquet" in str(ei.value).lower()


def test_wrong_schema_parquet_is_rejected(tmp_path):
    # a valid parquet file but missing the required OHLCV columns
    df = pd.DataFrame({"foo": [1, 2], "bar": [3, 4]})
    p = tmp_path / "wrong_schema.parquet"
    df.to_parquet(p, index=False)
    with pytest.raises(store.ParquetValidationError) as ei:
        store.load_bars(p)
    msg = str(ei.value).lower()
    assert "column" in msg or "schema" in msg


def test_valid_parquet_still_loads(tmp_path):
    p = tmp_path / "good.parquet"
    store.save_bars(_BARS, p)
    assert store.load_bars(p) == _BARS


def test_cache_with_corrupt_file_falls_back_or_errors_clearly(tmp_path):
    # if the cached file is corrupt, the provider must not return silent bad data
    delegate = _CountingProvider(_BARS)
    cp = CachedProvider(delegate, cache_dir=tmp_path)
    cp.get_bars("2330", "1d", "2026-05-01", "2026-05-05")  # populate cache
    # corrupt the cached parquet
    cached = list(Path(tmp_path).rglob("*.parquet"))[0]
    cached.write_bytes(b"corrupted")
    # a corrupt cache must be re-fetched (not silently returned as bad data)
    again = cp.get_bars("2330", "1d", "2026-05-01", "2026-05-05")
    assert again == _BARS
    assert delegate.calls == 2  # re-fetched because cache was unreadable
