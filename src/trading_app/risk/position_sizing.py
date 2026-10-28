"""Deterministic position sizing: how much to buy is computed from the rules, never guessed."""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal

from trading_app.risk.rules import TradingRules

MARKETS = ("stocks", "crypto")
MAX_DECIMALS = 12


class SizingError(ValueError):
    """The trade idea breaks the rules or has inconsistent prices."""


@dataclass(frozen=True)
class PositionPlan:
    symbol: str
    market: str
    quantity: float
    entry: float
    stop: float
    target: float | None
    position_value: float
    risk_amount: float
    risk_pct: float
    reward_risk: float | None
    meets_min_reward_risk: bool | None
    capped_by: str
    warnings: tuple[str, ...]


def size_position(
    rules: TradingRules,
    *,
    symbol: str,
    market: str,
    entry: float,
    stop: float,
    target: float | None = None,
    decimals: int = 0,
) -> PositionPlan:
    """Size a long position so a stop-out loses at most risk_per_trade_pct of capital.

    The quantity is the smaller of what the risk budget allows and what the
    max_position_pct cap allows, rounded down to `decimals` (0 = whole shares).
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise SizingError("symbol must not be empty")
    _check_symbol(rules, symbol, market)
    _check_prices(entry, stop, target)
    if not 0 <= decimals <= MAX_DECIMALS:
        raise SizingError(f"decimals must be between 0 and {MAX_DECIMALS} (got {decimals})")

    unit_risk = entry - stop
    risk_budget = rules.capital * rules.risk_per_trade_pct / 100
    position_cap = rules.capital * rules.max_position_pct / 100
    by_risk = risk_budget / unit_risk
    by_cap = position_cap / entry
    capped_by = "risk" if by_risk <= by_cap else "max_position"
    quantity = _round_down(min(by_risk, by_cap), decimals)

    warnings = []
    if quantity == 0:
        limit = (
            f"A risk budget of {risk_budget:.2f}"
            if capped_by == "risk"
            else f"A max position of {position_cap:.2f}"
        )
        warnings.append(
            f"{limit} {rules.currency} cannot buy one unit at {entry:g} "
            f"with {decimals} decimals; skip this candidate"
        )

    reward_risk = None
    meets_min_reward_risk = None
    if target is not None:
        reward_risk = round((target - entry) / unit_risk, 4)
        meets_min_reward_risk = reward_risk >= rules.min_reward_risk
        if not meets_min_reward_risk:
            warnings.append(
                f"reward/risk {reward_risk:.2f} is below your minimum of {rules.min_reward_risk:g}"
            )

    risk_amount = quantity * unit_risk
    return PositionPlan(
        symbol=symbol,
        market=market,
        quantity=quantity,
        entry=entry,
        stop=stop,
        target=target,
        position_value=round(quantity * entry, 4),
        risk_amount=round(risk_amount, 4),
        risk_pct=round(risk_amount / rules.capital * 100, 4),
        reward_risk=reward_risk,
        meets_min_reward_risk=meets_min_reward_risk,
        capped_by=capped_by,
        warnings=tuple(warnings),
    )


def _check_symbol(rules: TradingRules, symbol: str, market: str) -> None:
    if market not in MARKETS:
        raise SizingError(f"market must be one of {', '.join(MARKETS)} (got {market!r})")
    if not getattr(rules, market):
        raise SizingError(f"The {market} market is disabled in your rules")
    if symbol in rules.blocked_symbols:
        raise SizingError(f"{symbol} is blocked in your rules")
    if rules.allowed_symbols and symbol not in rules.allowed_symbols:
        raise SizingError(f"{symbol} is not in your allowed_symbols list")


def _check_prices(entry: float, stop: float, target: float | None) -> None:
    for name, value in (("entry", entry), ("stop", stop), ("target", target)):
        if value is not None and not math.isfinite(value):
            raise SizingError(f"{name} must be a finite number (got {value})")
    if entry <= 0:
        raise SizingError(f"entry must be greater than 0 (got {entry:g})")
    if stop <= 0:
        raise SizingError(f"stop must be greater than 0 (got {stop:g})")
    if stop >= entry:
        raise SizingError(
            f"stop ({stop:g}) must be below entry ({entry:g}): only long positions are supported"
        )
    if target is not None and target <= entry:
        raise SizingError(f"target ({target:g}) must be above entry ({entry:g})")


def _round_down(quantity: float, decimals: int) -> float:
    rounded = Decimal(str(quantity)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_DOWN)
    return int(rounded) if decimals == 0 else float(rounded)
