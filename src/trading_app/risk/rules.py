"""Load and validate the user's trading rules from a TOML file."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HORIZONS = ("intraday", "swing", "position")


class RulesError(ValueError):
    """The rules file is missing, malformed, or holds an invalid value."""


@dataclass(frozen=True)
class TradingRules:
    capital: float
    currency: str
    risk_per_trade_pct: float
    max_position_pct: float
    max_daily_loss_pct: float
    min_reward_risk: float
    horizon: str
    min_holding_days: int
    max_holding_days: int
    max_candidates: int
    stocks: bool
    crypto: bool
    allowed_symbols: tuple[str, ...]
    blocked_symbols: tuple[str, ...]


def load_rules(path: Path | str) -> TradingRules:
    path = Path(path)
    if not path.is_file():
        raise RulesError(
            f"Rules file not found: {path}. "
            "Copy config/rules.example.toml to config/rules.toml and edit it."
        )
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise RulesError(f"Rules file {path} is not valid TOML: {exc}") from exc
    return _parse(data)


def _parse(data: dict[str, Any]) -> TradingRules:
    min_days = _integer(data, "strategy", "min_holding_days", minimum=0)
    max_days = _integer(data, "strategy", "max_holding_days", minimum=0)
    if max_days < min_days:
        raise RulesError(
            f"strategy.max_holding_days ({max_days}) must be >= "
            f"strategy.min_holding_days ({min_days})"
        )

    horizon = _field(data, "strategy", "horizon")
    if horizon not in HORIZONS:
        raise RulesError(
            f"strategy.horizon must be one of {', '.join(HORIZONS)} (got {horizon!r})"
        )

    stocks = _boolean(data, "markets", "stocks")
    crypto = _boolean(data, "markets", "crypto")
    if not (stocks or crypto):
        raise RulesError("Enable at least one market in [markets] (stocks or crypto)")

    allowed = _symbols(data, "allowed_symbols")
    blocked = _symbols(data, "blocked_symbols")
    overlap = sorted(set(allowed) & set(blocked))
    if overlap:
        raise RulesError(f"Symbols cannot be both allowed and blocked: {', '.join(overlap)}")

    currency = _field(data, "account", "currency")
    if not isinstance(currency, str) or not currency.strip():
        raise RulesError("account.currency must be a non-empty text value")

    return TradingRules(
        capital=_number(data, "account", "capital"),
        currency=currency.strip().upper(),
        risk_per_trade_pct=_number(data, "risk", "risk_per_trade_pct", maximum=100),
        max_position_pct=_number(data, "risk", "max_position_pct", maximum=100),
        max_daily_loss_pct=_number(data, "risk", "max_daily_loss_pct", maximum=100),
        min_reward_risk=_number(data, "risk", "min_reward_risk"),
        horizon=horizon,
        min_holding_days=min_days,
        max_holding_days=max_days,
        max_candidates=_integer(data, "strategy", "max_candidates", minimum=1),
        stocks=stocks,
        crypto=crypto,
        allowed_symbols=allowed,
        blocked_symbols=blocked,
    )


def _field(data: dict[str, Any], section: str, key: str) -> Any:
    try:
        return data[section][key]
    except (KeyError, TypeError):
        raise RulesError(f"Missing field {section}.{key}") from None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _number(
    data: dict[str, Any], section: str, key: str, *, maximum: float | None = None
) -> float:
    value = _field(data, section, key)
    if not _is_number(value) or value <= 0 or (maximum is not None and value > maximum):
        limit = f" and at most {maximum:g}" if maximum is not None else ""
        raise RulesError(f"{section}.{key} must be a number greater than 0{limit} (got {value!r})")
    return float(value)


def _integer(data: dict[str, Any], section: str, key: str, *, minimum: int) -> int:
    value = _field(data, section, key)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise RulesError(f"{section}.{key} must be a whole number >= {minimum} (got {value!r})")
    return value


def _boolean(data: dict[str, Any], section: str, key: str) -> bool:
    value = _field(data, section, key)
    if not isinstance(value, bool):
        raise RulesError(f"{section}.{key} must be true or false (got {value!r})")
    return value


def _symbols(data: dict[str, Any], key: str) -> tuple[str, ...]:
    value = _field(data, "markets", key)
    if not isinstance(value, list) or not all(isinstance(s, str) and s.strip() for s in value):
        raise RulesError(f"markets.{key} must be a list of symbols, e.g. [\"AAPL\", \"BTC\"]")
    return tuple(s.strip().upper() for s in value)
