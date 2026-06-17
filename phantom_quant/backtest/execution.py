"""Execution realism: order-status validation + fill gating.

The backtest engine must not silently fill orders that could not realistically
fill on the given bar. This module separates two concerns:

1. *Validation* — is the order structurally well-formed? (side, qty, type,
   limit_price). A malformed order is REJECTED — it can never fill.
2. *Gating* — given a well-formed order and the bar it is evaluated on, could it
   realistically fill? A market order needs real trading activity on the bar
   (volume > 0). A limit order additionally needs the bar's price range to reach
   the limit (no look-ahead, no impossible price). A buy must be affordable and
   a sell must be covered by the held position. Anything that fails is GATED.

Only a FILLED decision mutates the portfolio. REJECTED/GATED orders are recorded
on the trade tape with their status and a human-readable reason, never filled.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from ..bars import Bar
from ..strategy import Order

_VALID_SIDES = ("buy", "sell")
_VALID_TYPES = ("market", "limit")


class FillStatus(str, Enum):
    """Outcome of evaluating an order against a bar.

    Subclasses ``str`` so existing string comparisons / JSON serialization keep
    working and report code can render it directly.
    """

    FILLED = "filled"
    REJECTED = "rejected"   # structurally invalid — can never fill
    GATED = "gated"         # well-formed but not realistically fillable on this bar


@dataclass(frozen=True)
class FillDecision:
    status: FillStatus
    price: float | None       # the price the order would fill at (None if not filled)
    reason: str               # human-readable explanation


def validate_order(order: Order) -> str | None:
    """Return a rejection reason if the order is structurally invalid, else None."""
    if order.side not in _VALID_SIDES:
        return f"invalid side {order.side!r}"
    if order.type not in _VALID_TYPES:
        return f"invalid order type {order.type!r}"
    if not isinstance(order.qty, int) or order.qty <= 0:
        return f"qty must be a positive int, got {order.qty!r}"
    if order.type == "limit":
        if order.limit_price is None:
            return "limit order requires a limit_price"
        if order.limit_price <= 0:
            return f"limit_price must be > 0, got {order.limit_price!r}"
    return None


def decide_fill(order: Order, bar: Bar, cash: Decimal, held: int, cost_fn) -> FillDecision:
    """Decide whether `order` fills on `bar`, and at what price.

    No look-ahead: a limit only fills if the bar's traded range reaches it, and
    fills at the limit price (a price actually achievable within the bar).
    """
    reason = validate_order(order)
    if reason is not None:
        return FillDecision(FillStatus.REJECTED, None, reason)

    # A bar with no trading activity cannot fill anything (halt / missing data).
    if bar.volume <= 0:
        return FillDecision(FillStatus.GATED, None, "no trading activity on bar (volume <= 0)")

    if order.type == "market":
        price = bar.close
    else:  # limit
        lp = float(order.limit_price)
        if order.side == "buy":
            # a buy limit fills only if price traded down to/below the limit
            if bar.low > lp:
                return FillDecision(
                    FillStatus.GATED, None,
                    f"buy limit {lp} below bar low {bar.low}; not reached")
        else:  # sell
            # a sell limit fills only if price traded up to/above the limit
            if bar.high < lp:
                return FillDecision(
                    FillStatus.GATED, None,
                    f"sell limit {lp} above bar high {bar.high}; not reached")
        price = lp

    if order.side == "buy":
        notional = Decimal(str(price)) * Decimal(order.qty)
        cost = cost_fn("buy", price, order.qty)
        if notional + cost > cash:
            return FillDecision(
                FillStatus.GATED, None,
                f"insufficient cash: need {notional + cost}, have {cash}")
    else:  # sell
        if order.qty > held:
            return FillDecision(
                FillStatus.GATED, None,
                f"cannot sell {order.qty}; only hold {held}")

    return FillDecision(FillStatus.FILLED, price, "ok")
