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

### Data sources (MCP servers)

`.mcp.json` declares two remote, read-only MCP servers for this project:

| Server | What it provides | Account |
|---|---|---|
| `coingecko` | Crypto prices, market cap, volume, trending coins | None (keyless public endpoint, shared rate limits) |
| `tradingview` | Economic and earnings calendars, screener, technical indicators, fundamentals, news | TradingView **Essential** plan or higher (public beta) |

1. Run `claude` in this folder and approve both servers when asked.
2. Run `/mcp`, select `tradingview` and log in with your TradingView account.

Without TradingView the agents fall back to official sources (Federal Reserve, BEA, Census, SEC)
and web search, with less market data.

## Research agents

Five read-only agents live in `.claude/agents/`. They can only search and read; a test
(`tests/test_agent_config.py`) fails if any of them gets a tool that can change files, run
commands or place orders.

| Agent | Researches |
|---|---|
| `macro-calendar` | Official US economic releases in the window (CPI, PPI, jobs, GDP, PCE, FOMC) |
| `fed-watcher` | Federal Reserve stance, decisions, minutes and speeches |
| `earnings-watcher` | Earnings, dividends and splits in the window; latest results |
| `stock-scout` | Long stock setups with entry, stop and target that fit your rules |
| `crypto-scout` | Crypto market read and long setups with entry, stop and target |

## Run the research

Inside `claude` in this folder:

```text
/trading-research
/trading-research only crypto
/trading-research tech stocks, en español
```

The skill only runs when you invoke it. It validates your rules, launches the agents in
parallel, sizes every idea with `trading-app size` (the model never picks the quantity), and
writes `reports/<date>-<time>.md` with the candidates, the events to avoid in the window, the rejected
ideas and the data gaps. Reports are git-ignored. It never places orders.

## Automate it (Windows)

`scripts/run-daily.ps1` runs `claude -p "/trading-research"` without supervision and logs to
`reports/logs/`. It uses the `dontAsk` permission mode, so every tool call outside a short allow
list is denied. The run reads untrusted web pages, so the guard assumes an injected instruction
may try to leak data or run code, and closes the exits:

- **Web fetches** only reach official data domains (Federal Reserve, BEA, Census, BLS, SEC,
  CoinGecko, TradingView). Web search and the two data MCP servers stay available.
- **Writes** can only create Markdown files directly inside `reports/`: no code, no config.
- **Commands**: only `uv run trading-app`.

Claude Code always allows read-only shell commands such as `cat` inside the working directory,
so the run *can* read files in this repository. **Keep secrets (API keys) out of this folder.**
Tests fail if the script bypasses permissions or widens any of these rules.

```powershell
.\scripts\run-daily.ps1 -DryRun    # print the exact command without running it
.\scripts\run-daily.ps1            # run it now
```

To run it every weekday at 7:30, from the repository root in PowerShell:

```powershell
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
           -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$((Resolve-Path scripts\run-daily.ps1).Path)`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 7:30am
Register-ScheduledTask -TaskName "MIGEANJE Trading Research" -Action $action -Trigger $trigger
```

Every run uses your Claude plan. Remove it with `Unregister-ScheduledTask -TaskName "MIGEANJE Trading Research"`.

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

## Position sizing

"How much to buy" is computed by code, never by the model. For a long trade:

- **Risk budget** = `capital × risk_per_trade_pct / 100`, so a stop-out never loses more than that.
- **Quantity** = the smaller of `risk budget / (entry − stop)` and `capital × max_position_pct / 100 / entry`,
  rounded **down** (whole shares by default, `--decimals` for crypto).
- With a `--target`, the reward/risk ratio is checked against `min_reward_risk`.

```bash
uv run trading-app rules    # validate config/rules.toml and print it as JSON
uv run trading-app size --symbol AAPL --market stocks --entry 190 --stop 182 --target 210
uv run trading-app size --symbol BTC --market crypto --entry 60000 --stop 54000 --decimals 6
```

The plan is printed as JSON (`quantity`, `position_value`, `risk_amount`, `risk_pct`, `reward_risk`,
`meets_min_reward_risk`, `capped_by`, `warnings`). A trade that breaks your rules (blocked symbol,
disabled market, stop above entry, etc.) exits with code 1 and the reason on stderr.
Only long positions are supported.
