# MIGEANJE Trading App

A rule-driven market research assistant that runs inside [Claude Code](https://code.claude.com).
You write your trading rules once; specialized research agents (macro calendar, Federal Reserve,
earnings, stock opportunities, crypto) gather information, and the result is one daily report
with a short list of candidates: why, when to enter, when to exit, how much to allocate, and
which events to avoid.

> **This is a research tool, not financial advice.** Language models can be wrong.
> Validate any idea on a paper-trading account before risking real money.

## How it is built

| Layer | What it does | Where |
|---|---|---|
| Rules | Your capital, risk limits, horizon and markets, in one file | `config/rules.toml` |
| Risk code | Deterministic, tested position sizing (the model never decides "how much") | `src/trading_app/risk/` |
| Research | Read-only agents that only consult data sources | `.claude/agents/` |

## Setup

Requirements: Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp config/rules.example.toml config/rules.toml   # then edit your own values
uv run pytest
```

`config/rules.toml` is git-ignored: this repository is public, and your capital and limits stay on your machine.

## Rules reference

| Section | Field | Meaning |
|---|---|---|
| `account` | `capital`, `currency` | Budget the agents may plan with |
| `risk` | `risk_per_trade_pct` | Max % of capital lost if one trade hits its stop |
| `risk` | `max_position_pct` | Max % of capital in a single position |
| `risk` | `max_daily_loss_pct` | Stop opening trades once daily losses reach this % |
| `risk` | `min_reward_risk` | Minimum expected reward/risk ratio for a candidate |
| `strategy` | `horizon` | `intraday`, `swing` or `position` |
| `strategy` | `min_holding_days`, `max_holding_days` | Expected holding period |
| `strategy` | `max_candidates` | How many candidates the report may propose |
| `markets` | `stocks`, `crypto` | Which markets are enabled (at least one) |
| `markets` | `allowed_symbols`, `blocked_symbols` | Optional allow/deny lists (empty allow list = any) |

Invalid rules are rejected with the name of the offending field.
