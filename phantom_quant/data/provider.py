"""Bar providers. CsvProvider is the offline source used by every test — no
broker, no network. ShioajiProvider (live fetch) is added later and is optional.
"""
from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from pathlib import Path

from ..bars import Bar


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
