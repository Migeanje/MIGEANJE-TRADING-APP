from pathlib import Path

import pytest

from trading_app.risk.rules import RulesError, TradingRules, load_rules

EXAMPLE_RULES = Path(__file__).resolve().parents[1] / "config" / "rules.example.toml"

VALID_TOML = """
[account]
capital = 1000.0
currency = "USD"

[risk]
risk_per_trade_pct = 1.0
max_position_pct = 20.0
max_daily_loss_pct = 3.0
min_reward_risk = 2.0

[strategy]
horizon = "swing"
min_holding_days = 2
max_holding_days = 20
max_candidates = 5

[markets]
stocks = true
crypto = true
allowed_symbols = ["aapl", "btc"]
blocked_symbols = []
"""


def write_rules(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "rules.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_shipped_example_is_valid():
    rules = load_rules(EXAMPLE_RULES)

    assert isinstance(rules, TradingRules)
    assert rules.capital == 1000.0
    assert rules.risk_per_trade_pct == 1.0
    assert rules.horizon == "swing"


def test_loads_every_field(tmp_path):
    rules = load_rules(write_rules(tmp_path, VALID_TOML))

    assert rules.capital == 1000.0
    assert rules.currency == "USD"
    assert rules.risk_per_trade_pct == 1.0
    assert rules.max_position_pct == 20.0
    assert rules.max_daily_loss_pct == 3.0
    assert rules.min_reward_risk == 2.0
    assert rules.horizon == "swing"
    assert (rules.min_holding_days, rules.max_holding_days) == (2, 20)
    assert rules.max_candidates == 5
    assert rules.stocks is True
    assert rules.crypto is True


def test_symbols_are_normalized_to_uppercase(tmp_path):
    rules = load_rules(write_rules(tmp_path, VALID_TOML))

    assert rules.allowed_symbols == ("AAPL", "BTC")


def test_missing_file_points_to_the_example(tmp_path):
    with pytest.raises(RulesError, match="rules.example.toml"):
        load_rules(tmp_path / "rules.toml")


def test_missing_field_is_named(tmp_path):
    content = VALID_TOML.replace("risk_per_trade_pct = 1.0\n", "")

    with pytest.raises(RulesError, match=r"risk\.risk_per_trade_pct"):
        load_rules(write_rules(tmp_path, content))


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        ("capital = 1000.0", "capital = 0", "account.capital"),
        ("risk_per_trade_pct = 1.0", "risk_per_trade_pct = 0", "risk.risk_per_trade_pct"),
        ("max_position_pct = 20.0", "max_position_pct = 150", "risk.max_position_pct"),
        ("max_daily_loss_pct = 3.0", "max_daily_loss_pct = -1", "risk.max_daily_loss_pct"),
        ("min_reward_risk = 2.0", "min_reward_risk = 0", "risk.min_reward_risk"),
        ('horizon = "swing"', 'horizon = "yolo"', "strategy.horizon"),
        ("max_holding_days = 20", "max_holding_days = 1", "strategy.max_holding_days"),
        ("max_candidates = 5", "max_candidates = 0", "strategy.max_candidates"),
        ('capital = 1000.0', 'capital = "mucho"', "account.capital"),
    ],
)
def test_invalid_values_are_rejected(tmp_path, old, new, field):
    with pytest.raises(RulesError, match=field.replace(".", r"\.")):
        load_rules(write_rules(tmp_path, VALID_TOML.replace(old, new)))


def test_at_least_one_market_must_be_enabled(tmp_path):
    content = VALID_TOML.replace("stocks = true", "stocks = false").replace(
        "crypto = true", "crypto = false"
    )

    with pytest.raises(RulesError, match="markets"):
        load_rules(write_rules(tmp_path, content))


def test_symbol_cannot_be_allowed_and_blocked(tmp_path):
    content = VALID_TOML.replace("blocked_symbols = []", 'blocked_symbols = ["AAPL"]')

    with pytest.raises(RulesError, match="AAPL"):
        load_rules(write_rules(tmp_path, content))


def test_malformed_toml_is_reported(tmp_path):
    with pytest.raises(RulesError, match="TOML"):
        load_rules(write_rules(tmp_path, "[account\ncapital = "))
