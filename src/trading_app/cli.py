"""Command line entry point, used by the research skill and by humans."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from trading_app.risk.position_sizing import MARKETS, SizingError, size_position
from trading_app.risk.rules import RulesError, load_rules

DEFAULT_RULES = Path("config") / "rules.toml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-app",
        description="Validate your trading rules and size positions that respect them.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    rules = commands.add_parser("rules", help="Validate the rules file and print it as JSON")
    _add_rules_option(rules)

    size = commands.add_parser(
        "size", help="Compute a long position size that respects your rules, as JSON"
    )
    _add_rules_option(size)
    size.add_argument("--symbol", required=True, help="Ticker, e.g. AAPL or BTC")
    size.add_argument("--market", required=True, choices=MARKETS)
    size.add_argument("--entry", required=True, type=float, help="Planned entry price")
    size.add_argument("--stop", required=True, type=float, help="Stop-loss price (below entry)")
    size.add_argument("--target", type=float, help="Take-profit price (above entry)")
    size.add_argument(
        "--decimals",
        type=int,
        default=0,
        help="Quantity decimals: 0 for whole shares (default), e.g. 6 for crypto",
    )
    return parser


def _add_rules_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--rules",
        type=Path,
        default=DEFAULT_RULES,
        help=f"Path to the rules file (default: {DEFAULT_RULES})",
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rules = load_rules(args.rules)
        if args.command == "rules":
            result = asdict(rules)
        else:
            plan = size_position(
                rules,
                symbol=args.symbol,
                market=args.market,
                entry=args.entry,
                stop=args.stop,
                target=args.target,
                decimals=args.decimals,
            )
            result = asdict(plan)
    except (RulesError, SizingError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0
