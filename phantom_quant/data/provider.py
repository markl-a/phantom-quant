"""Bar providers. CsvProvider is the offline source used by every test — no
broker, no network. ShioajiProvider (live fetch) is added later and is optional.

CachedProvider wraps any other provider with an on-disk Parquet cache:
fetch-once, backtest-many. A cache hit returns identical bars without
re-fetching; a corrupt cache file is detected and transparently re-fetched
(never returned as silent bad data).
"""
from __future__ import annotations

import csv
import re
from abc import ABC, abstractmethod
from pathlib import Path

from ..bars import Bar
from . import store


class BarProvider(ABC):
    @abstractmethod
    def get_bars(self, symbol: str, timeframe: str, start: str, end: str) -> list[Bar]:
        raise NotImplementedError


class CsvProvider(BarProvider):
    """Reads a CSV with header: ts,symbol,open,high,low,close,volume."""

    def __init__(self, csv_path: str | Path):
        self.path = Path(csv_path)

    def get_bars(self, symbol: str, timeframe: str, start: str, end: str) -> list[Bar]:
        out: list[Bar] = []
        with self.path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row["symbol"] != symbol:
                    continue
                if not (start <= row["ts"] <= end):
                    continue
                out.append(Bar(
                    ts=row["ts"], symbol=row["symbol"],
                    open=float(row["open"]), high=float(row["high"]),
                    low=float(row["low"]), close=float(row["close"]),
                    volume=int(row["volume"]),
                ))
        out.sort(key=lambda b: b.ts)
        return out


def _safe(token: str) -> str:
    """Make a path-safe token from a request field."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(token))


class CachedProvider(BarProvider):
    """Disk-backed cache around a delegate provider.

    The cache key is (symbol, timeframe, start, end); each unique request maps to
    one Parquet file under ``cache_dir``. On a cache hit the bars are loaded from
    disk (no delegate call). If the cached file is unreadable/corrupt it is
    re-fetched — silent bad data is never returned.
    """

    def __init__(self, delegate: BarProvider, cache_dir: str | Path):
        self.delegate = delegate
        self.cache_dir = Path(cache_dir)

    def _cache_path(self, symbol: str, timeframe: str, start: str, end: str) -> Path:
        name = "_".join(_safe(t) for t in (symbol, timeframe, start, end)) + ".parquet"
        return self.cache_dir / name

    def get_bars(self, symbol: str, timeframe: str, start: str, end: str) -> list[Bar]:
        path = self._cache_path(symbol, timeframe, start, end)
        if path.exists():
            try:
                return store.load_bars(path)
            except store.ParquetValidationError:
                # corrupt cache: drop it and re-fetch rather than serve bad data
                path.unlink(missing_ok=True)
        bars = self.delegate.get_bars(symbol, timeframe, start, end)
        store.save_bars(bars, path)
        return bars
