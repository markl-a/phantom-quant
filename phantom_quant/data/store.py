"""Local parquet cache: fetch-once, backtest-many, offline + deterministic.

Parquet is validated on load: a corrupt file or one missing the OHLCV schema
raises ``ParquetValidationError`` rather than letting silent bad data flow into
a backtest. (An honest backtest must never run on quietly-wrong data.)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..bars import Bar

_COLS = ["ts", "symbol", "open", "high", "low", "close", "volume"]


class ParquetValidationError(Exception):
    """Raised when a parquet file is unreadable or has the wrong schema."""


def save_bars(bars: list[Bar], path: str | Path) -> None:
    df = pd.DataFrame([[b.ts, b.symbol, b.open, b.high, b.low, b.close, b.volume]
                       for b in bars], columns=_COLS)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _read_validated(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    try:
        df = pd.read_parquet(p)
    except Exception as e:  # corrupt/non-parquet bytes, truncated file, etc.
        raise ParquetValidationError(
            f"could not read parquet {p}: {e}") from e
    missing = [c for c in _COLS if c not in df.columns]
    if missing:
        raise ParquetValidationError(
            f"parquet {p} is missing required column(s): {missing}; "
            f"expected schema {_COLS}, got {list(df.columns)}")
    return df


def load_bars(path: str | Path) -> list[Bar]:
    df = _read_validated(path)
    try:
        return [Bar(ts=str(r.ts), symbol=str(r.symbol), open=float(r.open),
                    high=float(r.high), low=float(r.low), close=float(r.close),
                    volume=int(r.volume)) for r in df.itertuples(index=False)]
    except (TypeError, ValueError) as e:
        raise ParquetValidationError(
            f"parquet {Path(path)} has the right columns but bad cell types: {e}") from e
