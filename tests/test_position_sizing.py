import pytest

from trading_app.risk.position_sizing import SizingError, size_position
from trading_app.risk.rules import TradingRules


def make_rules(**overrides) -> TradingRules:
    values = dict(
        capital=1000.0,
        currency="USD",
        risk_per_trade_pct=1.0,  # risk budget: 10 USD
        max_position_pct=20.0,  # position cap: 200 USD
        max_daily_loss_pct=3.0,
        min_reward_risk=2.0,
        horizon="swing",
        min_holding_days=2,
        max_holding_days=20,
        max_candidates=5,
        stocks=True,
        crypto=True,
        allowed_symbols=(),
        blocked_symbols=(),
    )
    values.update(overrides)
    return TradingRules(**values)


def test_quantity_is_limited_by_risk_budget():
    plan = size_position(make_rules(), symbol="abc", market="stocks", entry=50, stop=45)

    assert plan.symbol == "ABC"
    assert plan.quantity == 2  # 10 USD budget / 5 USD per share
    assert plan.capped_by == "risk"
    assert plan.position_value == pytest.approx(100)
    assert plan.risk_amount == pytest.approx(10)
    assert plan.risk_pct == pytest.approx(1.0)


def test_quantity_is_capped_by_max_position_size():
    plan = size_position(make_rules(), symbol="ABC", market="stocks", entry=100, stop=99)

    assert plan.quantity == 2  # risk allows 10 shares, but 20% of capital buys only 2
    assert plan.capped_by == "max_position"
    assert plan.position_value == pytest.approx(200)
    assert plan.risk_amount == pytest.approx(2)


def test_whole_units_are_rounded_down():
    plan = size_position(make_rules(), symbol="ABC", market="stocks", entry=30, stop=27)

    assert plan.quantity == 3  # 3.33 shares rounded down, never up


def test_fractional_units_are_rounded_down_to_requested_decimals():
    plan = size_position(
        make_rules(), symbol="BTC", market="crypto", entry=60000, stop=54000, decimals=6
    )

    assert plan.quantity == pytest.approx(0.001666)
    assert plan.risk_amount <= 10


def test_reward_risk_is_reported_against_the_minimum():
    good = size_position(make_rules(), symbol="ABC", market="stocks", entry=50, stop=45, target=65)
    poor = size_position(make_rules(), symbol="ABC", market="stocks", entry=50, stop=45, target=55)

    assert good.reward_risk == pytest.approx(3.0)
    assert good.meets_min_reward_risk is True
    assert poor.reward_risk == pytest.approx(1.0)
    assert poor.meets_min_reward_risk is False
    assert any("reward/risk" in w for w in poor.warnings)


def test_without_target_reward_risk_is_unknown():
    plan = size_position(make_rules(), symbol="ABC", market="stocks", entry=50, stop=45)

    assert plan.reward_risk is None
    assert plan.meets_min_reward_risk is None


def test_too_small_budget_yields_zero_quantity_with_warning():
    plan = size_position(make_rules(), symbol="ABC", market="stocks", entry=500, stop=400)

    assert plan.quantity == 0
    assert plan.risk_amount == 0
    assert any("cannot buy" in w for w in plan.warnings)


def test_zero_quantity_warning_names_the_limit_that_blocks_it():
    # Risk allows 2 shares (10 / 5) but the 200 USD position cap cannot buy one at 300.
    plan = size_position(make_rules(), symbol="ABC", market="stocks", entry=300, stop=295)

    assert plan.quantity == 0
    assert plan.capped_by == "max_position"
    assert any("max position of 200.00 USD cannot buy" in w for w in plan.warnings)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (dict(entry=float("nan"), stop=45), "entry"),
        (dict(entry=float("inf"), stop=45), "entry"),
        (dict(entry=50, stop=float("nan")), "stop"),
        (dict(entry=50, stop=45, target=float("inf")), "target"),
        (dict(entry=50, stop=45, decimals=30), "decimals"),
    ],
)
def test_non_finite_prices_and_absurd_decimals_are_rejected(kwargs, message):
    with pytest.raises(SizingError, match=message):
        size_position(make_rules(), symbol="ABC", market="stocks", **kwargs)


def test_empty_symbol_is_rejected():
    with pytest.raises(SizingError, match="symbol"):
        size_position(make_rules(), symbol="  ", market="stocks", entry=50, stop=45)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (dict(entry=50, stop=50), "stop"),
        (dict(entry=50, stop=55), "stop"),
        (dict(entry=50, stop=45, target=50), "target"),
        (dict(entry=0, stop=-1), "entry"),
        (dict(entry=50, stop=0), "stop"),
    ],
)
def test_invalid_prices_are_rejected(kwargs, message):
    with pytest.raises(SizingError, match=message):
        size_position(make_rules(), symbol="ABC", market="stocks", **kwargs)


def test_blocked_symbol_is_rejected():
    rules = make_rules(blocked_symbols=("ABC",))

    with pytest.raises(SizingError, match="blocked"):
        size_position(rules, symbol="abc", market="stocks", entry=50, stop=45)


def test_symbol_outside_allow_list_is_rejected():
    rules = make_rules(allowed_symbols=("XYZ",))

    with pytest.raises(SizingError, match="allowed"):
        size_position(rules, symbol="ABC", market="stocks", entry=50, stop=45)


def test_disabled_market_is_rejected():
    rules = make_rules(crypto=False)

    with pytest.raises(SizingError, match="crypto"):
        size_position(rules, symbol="BTC", market="crypto", entry=60000, stop=54000, decimals=6)


def test_unknown_market_is_rejected():
    with pytest.raises(SizingError, match="market"):
        size_position(make_rules(), symbol="ABC", market="forex", entry=50, stop=45)
