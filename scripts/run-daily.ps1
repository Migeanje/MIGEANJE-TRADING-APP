<#
.SYNOPSIS
    Runs the trading research without supervision and saves a log.

.DESCRIPTION
    Meant for Windows Task Scheduler. Runs `claude -p "/trading-research"` from the repository
    root in dontAsk permission mode: every tool not listed in $AllowedTools is denied, so an
    unattended run can research and write its report, but cannot edit code, run other
    commands or place orders. File reads are not allowed either: the run fetches untrusted
    web pages, and an injected instruction must not be able to read local files and leak
    them. Logs go to reports/logs (git-ignored).

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
    "WebFetch",
    "Edit(reports/**)",
    "Bash(uv run trading-app *)",
    "mcp__coingecko__*",
    "mcp__tradingview__*"
)
$Arguments = @("-p", "/trading-research", "--permission-mode", "dontAsk", "--allowedTools") + $AllowedTools

if ($DryRun) {
    Write-Output ("claude " + ($Arguments -join " "))
    exit 0
}

$LogDir = Join-Path $Root "reports\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir ("{0:yyyy-MM-dd_HHmm}.log" -f (Get-Date))

& claude @Arguments 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $Log
exit $LASTEXITCODE
