"""Performance metrics + Markdown report. Every number is derived from the
equity curve / trades — independently re-computable (adversarially auditable).
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .backtest.engine import BacktestResult


def _q(x: Decimal, places: str = "0.0001") -> Decimal:
    return x.quantize(Decimal(places), ROUND_HALF_UP)


def metrics(result: BacktestResult) -> dict:
    curve = [v for _, v in result.equity_curve]
    start, end = curve[0], curve[-1]
    total_return = _q(end / start - 1, "0.0001")
    peak = curve[0]
    max_dd = Decimal("0")
    for v in curve:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak else Decimal("0")
        if dd > max_dd:
            max_dd = dd
    # Only *filled* orders are real trades. Gated/rejected orders are recorded on
    # the tape (for auditability) but must not inflate trade counts. Trades from
    # older results without a "status" field are treated as filled (back-compat).
    filled = [t for t in result.trades if t.get("status", "filled") == "filled"]
    sells = [t for t in filled if t["side"] == "sell"]
    return {
        "start_equity": start,
        "end_equity": end,
        "total_return": total_return,
        "max_drawdown": _q(max_dd, "0.0001"),
        "num_trades": len(filled),
        "num_closed": len(sells),
    }


def to_markdown(result: BacktestResult, meta: dict) -> str:
    m = metrics(result)
    pct = lambda d: f"{(d * 100):.2f}%"
    lines = [
        "# phantom-quant backtest",
        "",
        f"- strategy: `{meta.get('strategy', '?')}`  ·  symbol: `{meta.get('symbol', '?')}`",
        f"- start equity: {m['start_equity']}  →  end equity: {m['end_equity']}",
        f"- **total return: {pct(m['total_return'])}**",
        f"- max drawdown: {pct(m['max_drawdown'])}",
        f"- trades: {m['num_trades']} (closed: {m['num_closed']})",
        "",
        "_Skeleton strategy on cached data with 台股 costs — not investment advice, "
        "not a profitable edge. Re-run `pytest` to re-derive every number._",
    ]
    return "\n".join(lines)
