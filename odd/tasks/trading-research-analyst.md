# Trading research analyst (Phase 1) + paper trading (Phase 2)

Objective: a Claude Code project that turns the user's own rules into a daily, multi-agent market research report (stocks + crypto) with a short candidate list, and later practices on an Alpaca paper account.
Branch: `feat/phase1-research-analyst` · Delivery: `single-pr` (new personal repo, solo developer, no reviewers) · Test runner: `uv run pytest`
Constraint: the GitHub repo is PUBLIC — personal rules (capital), reports and credentials must never be committed.

## Specs

- **S1 — User rules as input.** From the reference video: "le das tus reglas fechas presupuesto qué puede operar y cuánto estás dispuesto a perder". Rules live in a machine-readable file that both the agents and the code read. The real file is git-ignored; only an example is committed (public repo).
- **S2 — Research split across subagents.** "reparten la investigación en 10 subagentes calendarios económicos oficiales anuncios de la reserva federal resultados de empresas y oportunidades en acciones". Assumption: 5 specialized read-only agents instead of 10 (macro calendar, Fed, earnings, stock opportunities, crypto) to limit token spend.
- **S3 — One consolidated document.** "lo junta todo en un solo documento y te da una lista corta de candidatos el porqué de cada una cuándo entrar cuándo salir cuánto poner y qué eventos evitar".
- **S4 — Paper account first.** "ten en cuenta que los agentes de guía pueden equivocarse por eso primero usa una cuenta de prueba en alpaca juega con acciones reales pero con dinero falso".
- **S5 — Crypto and stocks coverage.** User: "quiero armar un agente orientado a la inversioo metrica real de todo lo referente a inversion cripto bolsa".
- **S6 — Position size is computed by code, not by the model.** Assumption (proposed by the assistant, not objected to by the user): "cuánto poner" comes from a deterministic formula over the user's rules (risk per trade / distance to stop, capped by max position size), covered by tests.
- **S7 — Automated.** User: "para que tenga que hacerlo automatizado".

## Tasks

| ID | Specs | Scope | Route | Status | Evidence |
|----|-------|-------|-------|--------|----------|
| T1 | S1 | Project scaffold (`pyproject.toml`, `.gitignore`, README) + rules example + rules loader/validator with tests | inline (no writer trigger: single unit, <100 lines of logic) | pending | |
| T2 | S3, S6 | Position sizing domain + `trading-app size` CLI + tests | inline | pending | |
| T3 | S2, S5 | 5 read-only research agents in `.claude/agents/` + project `.mcp.json` (CoinGecko, TradingView) | inline | pending | |
| T4 | S3 | `/trading-research` orchestrator skill + report format (`reports/`, git-ignored) | inline | pending | |
| T5 | S7 | Daily headless run script (`claude -p`) + Windows Task Scheduler instructions | inline | pending | |
| T6 | S4 | Alpaca paper-trading MCP (local, `ALPACA_PAPER_TRADE=true`) + per-order human approval | inline | blocked: needs the user's Alpaca paper API keys | |

## Log

- **L1 (2026-10-28, user, verbatim):** "una consulkta quiero armar un agente orientado a la inversioo  metrica real de todo lo referente a inversion cripto bolsa por e jemplo xtb etc donde se pueda  tener el analisis para esto entinedo que peude haber ya skills mcp exactos en los cuales ya puedo guiame  para que tenga que hacerlo automatizado por ejemplo https://docs.coingecko.com/ai-integration/mcp-server, https://docs.etherscan.io/build-with-ai/mcp, https://alpaca.markets/mcp-server, https://www.tradingview.com/mcp/docs,https://github.com/lazy-dinosaur/ccxt-mcp, https://mcpservers.org/servers/polygon-io/mcp_polygon estos son ejemplo obviamenete me gustaria armar mi propio agente para poder autoatizar mis inversiones"
- **L2 (2026-10-28, user, verbatim):** "https://vt.tiktok.com/ZSgpqaLu6/ este es en lo que me quiero basar"
- **L3 (2026-10-28, evidence):** Reference video (@miguel_silva.ia, 42 s) transcript, from its Spanish subtitles: "para los que hacen trading cloth acaba de matar todo el análisis a ojo te explico cómo funciona primero le das tus reglas fechas presupuesto qué puede operar y cuánto estás dispuesto a perder con eso o cloth code reparten la investigación en 10 subagentes calendarios económicos oficiales anuncios de la reserva federal resultados de empresas y oportunidades en acciones después lo junta todo en un solo documento y te da una lista corta de candidatos el porqué de cada una cuándo entrar cuándo salir cuánto poner y qué eventos evitar ten en cuenta que los agentes de guía pueden equivocarse por eso primero usa una cuenta de prueba en alpaca juega con acciones reales pero con dinero falso si quieres la guía de instalación ve al link de mi perfil y escribe la palabra trading en el buscador de mi página"
- **L4 (2026-10-28, user, verbatim):** "https://github.com/Migeanje/MIGEANJE-TRADING-APP ya tengo el repo y tenoog C:\Users\Miguel\Documents\GitHub\MIGEANJE-TRADING-APP la ruta donde esta"
- **L5 (2026-10-28, research evidence):** XTB discontinued its API on 2025-03-14 (help center: "API access is no longer available. The service was discontinued on March 14, 2025.") → XTB cannot be automated; execution there stays manual. Data-only MCPs: CoinGecko (official, keyless remote `https://mcp.api.coingecko.com/mcp`), Etherscan (official, keyless remote), TradingView (official beta, `https://mcp.tradingview.com/mcp`, OAuth, needs Essential plan or higher, no order placement), Massive (ex Polygon.io). Order-capable: Alpaca (official, local only, paper by default; Peru eligibility unverified), Binance (official, isolated sub-account). ccxt-mcp rejected (community, plaintext keys, no sandbox, "use all capital" default).
- **L6 (2026-10-28, decision):** Rules file format is TOML (`tomllib` is in the Python standard library → zero runtime dependencies). Python 3.13 + uv available locally. Repo confirmed public (GitHub API 200) → `config/rules.toml` and `reports/` are git-ignored.
- **L7 (2026-10-28, tracking):** Engram mirror `odd/trading-research-analyst/tasks` is PENDING — `mem_save` refused project `migeanje-trading-app` as "not backed by known context" (new repo). Resynchronize once Engram registers the project.
- **Next step:** T1.
