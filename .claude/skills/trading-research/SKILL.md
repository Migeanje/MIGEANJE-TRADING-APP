---
name: trading-research
description: Run the trading research workflow. Reads the user's rules, fans out to the read-only research agents, sizes every candidate with the risk code, and writes one report to reports/. Use when the user asks for the trading research, the daily report, or trade candidates.
argument-hint: "[optional focus, e.g. 'only crypto', 'tech stocks', 'en español']"
disable-model-invocation: true
allowed-tools: Read, Agent, Edit(reports/**), Bash(uv run trading-app *)
---

# Trading research

Produce one research report with a short list of candidates: why, when to enter, when to exit,
how much to allocate, and which events to avoid. This workflow **never places orders** and never
calls broker tools.

Optional focus from the user: $ARGUMENTS

## Step 0 — Load the rules (stop on failure)

Run `uv run trading-app rules`. It prints the validated rules as JSON.

- If it exits with code 1, stop. Show the error and tell the user to copy
  `config/rules.example.toml` to `config/rules.toml` and fill it in. Never continue with
  assumed or default rules.
- Today's date comes from your environment. The analysis window runs from today to today +
  `max_holding_days` (calendar days).

## Step 1 — Research in parallel

In a **single message**, launch these agents with the Agent tool so they run in parallel. Give
each one today's date, the window, the rules JSON and the user's focus (if any):

- `macro-calendar`: always.
- `fed-watcher`: always.
- `stock-scout`: only if `stocks` is true. Ask for 2 × `max_candidates` ideas.
- `crypto-scout`: only if `crypto` is true. Ask for 2 × `max_candidates` ideas.

## Step 2 — Earnings check

When `stock-scout` returns stock ideas, launch `earnings-watcher` with those symbols.

## Step 3 — Size every candidate with the risk code

For each idea, run exactly the levels the scout proposed:

```
uv run trading-app size --symbol <SYMBOL> --market <stocks|crypto> --entry <E> --stop <S> --target <T>
```

Add `--decimals 6` for crypto. Then:

- Exit code 1 → reject the idea and quote the reason from stderr.
- `quantity` 0, or `meets_min_reward_risk` false → reject the idea with that reason.
- Copy `quantity`, `position_value`, `risk_amount`, `risk_pct`, `capped_by` and `warnings`
  exactly as printed. Never compute, adjust, or round a quantity yourself.

## Step 4 — Select

Keep at most `max_candidates` ideas. Rank by reward/risk, strength of the thesis, and fewest
scheduled events inside the holding period; say in one line why the order is what it is. For
every candidate, list the events in the window it should avoid (macro releases, Fed dates,
earnings), using the agents' tables. Carry every data gap the agents reported into the report.

## Step 5 — Write the report

Write `reports/<YYYY-MM-DD>.md` (add `-<HHMM>` if that file already exists). Write it in
English unless the focus asks for another language. Use this structure:

```markdown
# Trading research — <date>

> Research only, not financial advice. Models can be wrong: validate on a paper account first.

**Rules used:** capital <capital> <currency> · risk/trade <risk_per_trade_pct>% ·
max position <max_position_pct>% · daily loss limit <max_daily_loss_pct>% ·
min reward/risk <min_reward_risk> · <horizon>, <min_holding_days>–<max_holding_days> days · markets: <enabled>
**Window:** <start> → <end>

## Summary
3–5 bullets: market regime, main risks this window, number of candidates.

## Candidates
| # | Symbol | Market | Why | Entry | Stop | Target | R/R | Quantity | Position | Risk (<currency> / %) |

### 1. <SYMBOL>
- **Why:** thesis in two or three lines.
- **When to enter:** the entry trigger.
- **When to exit:** stop at <stop> (idea invalidated), target at <target>, or after <max_holding_days> days.
- **How much:** <quantity> (<position_value> <currency>), capped by <capped_by>.
- **Events to avoid:** dates and events inside the holding period.
- **Warnings:** sizing warnings, if any.

## Events to avoid in the window
| Date | Time (ET) | Event | Impact | Affects |

## Federal Reserve
Stance and dates, from `fed-watcher`.

## Rejected ideas
| Symbol | Reason |

## Data gaps and sources
```

If no idea survives, write the report anyway with an empty candidate table and the reasons.

## Step 6 — Final message

Reply with the report path, the number of candidates and one line per candidate
(symbol, entry, stop, target, quantity). Nothing else.
