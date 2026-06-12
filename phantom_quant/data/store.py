"""Local parquet cache: fetch-once, backtest-many, offline + deterministic."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..bars import Bar

_COLS = ["ts", "symbol", "open", "high", "low", "close", "volume"]


def save_bars(bars: list[Bar], path: str | Path) -> None:
    df = pd.DataFrame([[b.ts, b.symbol, b.open, b.high, b.low, b.close, b.volume]
                       for b in bars], columns=_COLS)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def load_bars(path: str | Path) -> list[Bar]:
    df = pd.read_parquet(path)
    return [Bar(ts=str(r.ts), symbol=str(r.symbol), open=float(r.open),
                high=float(r.high), low=float(r.low), close=float(r.close),
                volume=int(r.volume)) for r in df.itertuples(index=False)]
