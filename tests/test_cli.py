import json
from pathlib import Path

from trading_app.cli import main

EXAMPLE_RULES = Path(__file__).resolve().parents[1] / "config" / "rules.example.toml"


def run(capsys, *argv):
    code = main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


def test_size_prints_the_plan_as_json(capsys):
    code, out, err = run(
        capsys, "size", "--rules", str(EXAMPLE_RULES),
        "--symbol", "abc", "--market", "stocks",
        "--entry", "50", "--stop", "45", "--target", "65",
    )

    assert code == 0
    assert err == ""
    plan = json.loads(out)
    assert plan["symbol"] == "ABC"
    assert plan["quantity"] == 2
    assert plan["capped_by"] == "risk"
    assert plan["reward_risk"] == 3.0
    assert plan["meets_min_reward_risk"] is True


def test_size_rejects_invalid_prices_with_exit_code_1(capsys):
    code, out, err = run(
        capsys, "size", "--rules", str(EXAMPLE_RULES),
        "--symbol", "ABC", "--market", "stocks", "--entry", "50", "--stop", "55",
    )

    assert code == 1
    assert out == ""
    assert "stop" in err


def test_size_rejects_nan_without_a_traceback(capsys):
    code, out, err = run(
        capsys, "size", "--rules", str(EXAMPLE_RULES),
        "--symbol", "ABC", "--market", "stocks", "--entry", "nan", "--stop", "45",
    )

    assert code == 1
    assert out == ""
    assert err.startswith("error: entry")


def test_missing_rules_file_explains_how_to_create_it(capsys, tmp_path):
    code, out, err = run(
        capsys, "size", "--rules", str(tmp_path / "rules.toml"),
        "--symbol", "ABC", "--market", "stocks", "--entry", "50", "--stop", "45",
    )

    assert code == 1
    assert out == ""
    assert "rules.example.toml" in err


def test_rules_prints_the_validated_rules_as_json(capsys):
    code, out, err = run(capsys, "rules", "--rules", str(EXAMPLE_RULES))

    assert code == 0
    assert err == ""
    rules = json.loads(out)
    assert rules["capital"] == 1000.0
    assert rules["risk_per_trade_pct"] == 1.0
    assert rules["allowed_symbols"] == []
