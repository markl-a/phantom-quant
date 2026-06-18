"""Performance metrics + Markdown report. Every number is derived from the
equity curve / trades — independently re-computable (adversarially auditable).
"""
from __future__ import annotations

import statistics
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from math import sqrt

from .backtest.engine import BacktestResult


def _q(x: Decimal, places: str = "0.0001") -> Decimal:
    return x.quantize(Decimal(places), ROUND_HALF_UP)


def _parse_equity_ts(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return datetime.combine(date.fromisoformat(s), datetime.min.time())


def _win_loss(filled: list[dict]) -> tuple[int, int]:
    """Count winning vs losing closed share-lot chunks via per-symbol FIFO.

    Quantity-aware: a sell consumes the front of the symbol's open-buy queue
    lot-by-lot, and each matched chunk counts a win (sell price > that lot's buy
    price) or a loss, so partial and multi-lot sells are counted correctly. Any
    over-sell remainder (shouldn't occur given gating) is ignored. The tape
    carries no per-lot cost, so this compares price vs basis only — an
    approximation, not realized PnL.
    """
    queues: dict[str, list] = {}
    wins = losses = 0

    for trade in filled:
        symbol = trade["symbol"]
        side = trade["side"]
        qty = int(trade["qty"])
        price = float(trade["price"])

        if side == "buy":
            if qty > 0:
                queues.setdefault(symbol, []).append([qty, price])
            continue

        lots = queues.get(symbol, [])
        remaining = qty
        while remaining > 0 and lots:
            lot = lots[0]
            matched = min(remaining, lot[0])
            if price > lot[1]:
                wins += 1
            else:
                losses += 1
            lot[0] -= matched
            remaining -= matched
            if lot[0] == 0:
                lots.pop(0)

    return wins, losses


def metrics(result: BacktestResult, *, risk_free: float = 0.0, periods_per_year: int = 252) -> dict:
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

    total_costs = sum((t["cost"] for t in filled), Decimal("0"))
    num_gated = sum(1 for t in result.trades if t.get("status", "filled") == "gated")
    num_rejected = sum(1 for t in result.trades if t.get("status", "filled") == "rejected")

    # Win/loss of CLOSED round-trips via quantity-aware FIFO pairing (see
    # _win_loss): an approximation off the tape, not realized PnL.
    wins, losses = _win_loss(filled)

    # Risk metrics:
    # - annualized Sharpe = mean(excess returns) / pstdev(rets) * sqrt(ppy)
    # - CAGR = (end / start) ** (1 / years) - 1
    # - annualized volatility = pstdev(rets) * sqrt(ppy)
    # risk_free defaults to 0 per annum and is converted to a per-period rate.
    # periods_per_year defaults to 252, Taiwan daily trading days. Edge cases are
    # graceful: <2 returns -> None; zero variance -> Sharpe None, vol 0.0;
    # unparseable dates -> fall back to bar-count / ppy years.
    rets = [float(curve[i]) / float(curve[i - 1]) - 1.0 for i in range(1, len(curve))]

    if len(rets) < 2:
        ann_vol = None
        sharpe = None
    else:
        sd = statistics.pstdev(rets)
        ann_vol = round(sd * sqrt(periods_per_year), 6)
        if sd == 0:
            sharpe = None
        else:
            rf_per = risk_free / periods_per_year
            excess_mean = statistics.mean(r - rf_per for r in rets)
            sharpe = round((excess_mean / sd) * sqrt(periods_per_year), 6)

    cagr = None
    if len(curve) >= 2:
        ts_first = result.equity_curve[0][0]
        ts_last = result.equity_curve[-1][0]
        years = None
        try:
            years = (_parse_equity_ts(ts_last) - _parse_equity_ts(ts_first)).total_seconds() / (365.25 * 24 * 3600)
        except ValueError:
            years = None
        if not years or years <= 0:
            years = len(rets) / periods_per_year if rets else None
        if years and years > 0:
            cagr = round((float(end) / float(start)) ** (1.0 / years) - 1.0, 6)

    return {
        "start_equity": start,
        "end_equity": end,
        "total_return": total_return,
        "max_drawdown": _q(max_dd, "0.0001"),
        "num_trades": len(filled),
        "num_closed": len(sells),
        "ending_cash": result.portfolio.cash,
        "realized_pnl": result.portfolio.realized,
        "total_costs": total_costs,
        "num_gated": num_gated,
        "num_rejected": num_rejected,
        "wins": wins,
        "losses": losses,
        "sharpe": sharpe,
        "cagr": cagr,
        "annualized_volatility": ann_vol,
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
        f"- sharpe: {m['sharpe']}  ·  CAGR: {pct(m['cagr']) if m['cagr'] is not None else 'n/a'}  ·  ann. vol: {m['annualized_volatility']}",
        f"- trades: {m['num_trades']} (closed: {m['num_closed']})",
        f"- realized PnL: {m['realized_pnl']}  ·  costs paid: {m['total_costs']}  ·  ending cash: {m['ending_cash']}",
        "",
        "_Skeleton strategy on cached data with 台股 costs — not investment advice, "
        "not a profitable edge. Re-run `pytest` to re-derive every number._",
    ]
    return "\n".join(lines)
