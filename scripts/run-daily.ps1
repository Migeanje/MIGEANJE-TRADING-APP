<#
.SYNOPSIS
    Runs the trading research without supervision and saves a log.

.DESCRIPTION
    Meant for Windows Task Scheduler. Runs `claude -p "/trading-research"` from the repository
    root in dontAsk permission mode: every tool call not covered by $AllowedTools is denied.

    The run fetches untrusted web pages, so the guard assumes an injected instruction may try
    to leak data or run code. Claude Code always allows read-only shell commands (cat, grep)
    inside the working directory, so the run can still read files in this repository. The
    guard closes the exits instead:
      - web fetches only reach the official data domains listed below;
      - writes can only create Markdown files directly inside reports/ (no code, no config);
      - the only command allowed is the project's own risk CLI.
    Keep secrets (API keys) out of this folder. Logs go to reports/logs (git-ignored).

.PARAMETER DryRun
    Print the command instead of running it.
#>
param(
    [switch]$DryRun
)

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$AllowedTools = @(
    "Agent",
    "WebSearch",
    "WebFetch(domain:www.federalreserve.gov)",
    "WebFetch(domain:www.bea.gov)",
    "WebFetch(domain:www.census.gov)",
    "WebFetch(domain:www.bls.gov)",
    "WebFetch(domain:www.sec.gov)",
    "WebFetch(domain:www.coingecko.com)",
    "WebFetch(domain:www.tradingview.com)",
    "Edit(reports/*.md)",
    "Bash(uv run trading-app *)",
    "mcp__coingecko__*",
    "mcp__tradingview__*"
)
$DisallowedTools = @("Read", "Grep", "Glob")

$Arguments = @("-p", "/trading-research", "--permission-mode", "dontAsk", "--allowedTools") +
    $AllowedTools + @("--disallowedTools") + $DisallowedTools

if ($DryRun) {
    $Printable = $Arguments | ForEach-Object {
        if ($_ -match '[\s()*]') { '"' + $_ + '"' } else { $_ }
    }
    Write-Output ("claude " + ($Printable -join " "))
    exit 0
}

$LogDir = Join-Path $Root "reports\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir ("{0:yyyy-MM-dd_HHmm}.log" -f (Get-Date))

& claude @Arguments 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $Log
exit $LASTEXITCODE
