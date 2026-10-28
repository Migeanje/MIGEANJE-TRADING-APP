"""Guards for the unattended daily run: narrow permissions, never a bypass."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run-daily.ps1"


def test_script_never_bypasses_permissions():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "bypassPermissions" not in text
    assert "dangerously-skip-permissions" not in text


def test_shell_access_is_limited_to_the_risk_cli():
    text = SCRIPT.read_text(encoding="utf-8")

    bash_rules = re.findall(r"Bash(\([^)]*\))?", text)
    assert bash_rules, "the run needs the risk CLI"
    assert set(bash_rules) == {"(uv run trading-app *)"}


@pytest.mark.skipif(shutil.which("powershell") is None, reason="Windows PowerShell not available")
def test_dry_run_prints_the_headless_command():
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), "-DryRun"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "claude -p /trading-research" in out
    assert "--permission-mode dontAsk" in out
    assert "Edit(reports/**)" in out
    assert "mcp__coingecko__*" in out
    assert "mcp__tradingview__*" in out
