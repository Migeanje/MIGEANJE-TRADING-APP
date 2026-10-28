"""Guards for the unattended daily run: narrow permissions, never a bypass.

Threat model: the run fetches untrusted web pages, so an injected instruction may try to
leak local data or run code. Claude Code always allows read-only shell commands (cat, grep)
inside the working directory, so the guard closes the exits instead: web fetches only reach
official data domains, writes only create Markdown reports, and the only command allowed is
the project's own risk CLI.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run-daily.ps1"

OFFICIAL_DOMAINS = {
    "www.federalreserve.gov",
    "www.bea.gov",
    "www.census.gov",
    "www.bls.gov",
    "www.sec.gov",
    "www.coingecko.com",
    "www.tradingview.com",
}


def script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_script_never_bypasses_permissions():
    text = script_text()

    assert "bypassPermissions" not in text
    assert "dangerously-skip-permissions" not in text


def test_web_fetch_only_reaches_official_domains():
    rules = re.findall(r'"WebFetch(\([^)]*\))?"', script_text())

    assert rules, "the agents need WebFetch for official sources"
    domains = set()
    for rule in rules:
        assert rule.startswith("(domain:"), "a bare WebFetch rule would allow any URL"
        domains.add(rule[len("(domain:"):-1])
    assert domains <= OFFICIAL_DOMAINS


def test_writes_only_create_markdown_reports():
    text = script_text()

    assert set(re.findall(r'"Edit(\([^)]*\))?"', text)) == {"(reports/*.md)"}
    assert '"Write' not in text


def test_shell_access_is_limited_to_the_risk_cli():
    bash_rules = re.findall(r"Bash(\([^)]*\))?", script_text())

    assert bash_rules, "the run needs the risk CLI"
    assert set(bash_rules) == {"(uv run trading-app *)"}


def test_file_search_tools_are_disallowed():
    text = script_text()

    disallowed = re.search(r"\$DisallowedTools = @\(([^)]*)\)", text)
    assert disallowed, "the script must declare $DisallowedTools"
    assert set(re.findall(r'"(\w+)"', disallowed.group(1))) == {"Read", "Grep", "Glob"}


@pytest.mark.skipif(shutil.which("powershell") is None, reason="Windows PowerShell not available")
def test_dry_run_prints_a_pasteable_headless_command():
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), "-DryRun"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert out.startswith("claude -p /trading-research --permission-mode dontAsk")
    assert '"Edit(reports/*.md)"' in out
    assert '"Bash(uv run trading-app *)"' in out
    assert '"WebFetch(domain:www.federalreserve.gov)"' in out
    assert '"mcp__coingecko__*"' in out
    assert "--disallowedTools Read Grep Glob" in out
