"""Guards for the /trading-research orchestrator skill."""

from pathlib import Path

from test_agent_config import RESEARCH_AGENTS, frontmatter

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "trading-research" / "SKILL.md"


def test_skill_only_runs_when_invoked_explicitly():
    fields = frontmatter(SKILL)

    assert fields["name"] == "trading-research"
    assert fields["disable-model-invocation"] == "true"


def test_skill_preapproves_only_reports_and_the_risk_cli():
    fields = frontmatter(SKILL)

    tools = {t.strip() for t in fields["allowed-tools"].split(",")}
    assert tools == {"Agent", "Edit(reports/*.md)", "Bash(uv run trading-app *)"}


def test_skill_delegates_to_every_research_agent():
    body = SKILL.read_text(encoding="utf-8")

    missing = [name for name in RESEARCH_AGENTS if f"`{name}`" not in body]
    assert not missing, f"the skill does not mention agents: {missing}"


def test_skill_uses_the_risk_code_for_rules_and_sizing():
    body = SKILL.read_text(encoding="utf-8")

    assert "uv run trading-app rules" in body
    assert "uv run trading-app size" in body


def test_skill_writes_the_report_to_the_ignored_reports_folder():
    body = SKILL.read_text(encoding="utf-8")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "reports/" in body
    assert "reports/*" in gitignore
