"""Guards for the Claude Code configuration: research agents must stay read-only."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".claude" / "agents"

RESEARCH_AGENTS = {"macro-calendar", "fed-watcher", "earnings-watcher", "stock-scout", "crypto-scout"}
READ_ONLY_TOOLS = {"Read", "Grep", "Glob", "WebSearch", "WebFetch"}
DATA_MCP_SERVERS = {"coingecko", "tradingview", "etherscan"}


def frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", f"{path.name} must start with YAML frontmatter"
    end = lines.index("---", 1)
    fields = {}
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def agent_files() -> list[Path]:
    return sorted(AGENTS_DIR.glob("*.md"))


def test_every_research_agent_exists():
    names = {frontmatter(p)["name"] for p in agent_files()}

    assert RESEARCH_AGENTS <= names


@pytest.mark.parametrize("path", agent_files(), ids=lambda p: p.stem)
def test_research_agents_only_get_read_only_tools(path):
    fields = frontmatter(path)
    if fields["name"] not in RESEARCH_AGENTS:
        pytest.skip("not a research agent")

    assert fields.get("description"), "an agent needs a description to be delegated to"
    tools = [t.strip() for t in fields["tools"].split(",")]
    for tool in tools:
        if tool.startswith("mcp__"):
            server = tool.split("__")[1]
            assert server in DATA_MCP_SERVERS, f"{tool} is not a data-only MCP server"
        else:
            assert tool in READ_ONLY_TOOLS, f"{tool} can change state; research agents are read-only"


def test_project_mcp_config_only_declares_data_servers():
    config = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))

    assert set(config["mcpServers"]) <= DATA_MCP_SERVERS
    for name, server in config["mcpServers"].items():
        assert server["type"] == "http", f"{name} should be a remote HTTP server"
        assert server["url"].startswith("https://"), f"{name} must use HTTPS"
