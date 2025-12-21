# Helper script to run SecBrain for Origin Protocol using environment variables.
param(
  [switch]$ReconOnly,
  [switch]$DryRun,
  [string]$KillSwitchFile = "targets/originprotocol/stop.flag"
)

# Ensure UTF-8 console output to avoid Rich/Colorama encoding errors on Windows
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

function Get-EnvOrEmpty([string]$name) {
  return [Environment]::GetEnvironmentVariable($name)
}

$rpcUrl = Get-EnvOrEmpty "RPC_URL"
if (-not $rpcUrl) {
  $rpcUrl = Get-EnvOrEmpty "RPC_FALLBACK"
}
$blockNumber = Get-EnvOrEmpty "RPC_BLOCK"
$chainId = if (Get-EnvOrEmpty "CHAIN_ID") { Get-EnvOrEmpty "CHAIN_ID" } else { "1" }

if (-not $rpcUrl) {
  Write-Error "Missing required RPC URL (RPC_URL or RPC_FALLBACK). Set and re-run."
  exit 1
}

$argsList = @(
  "secbrain", "run",
  "--scope", "targets/originprotocol/scope.yaml",
  "--program", "targets/originprotocol/program.json",
  "--workspace", "targets/originprotocol",
  "--chain-id", $chainId,
  "--exploit-iterations", "3",
  "--profit-threshold", "0.1"
)

if ($ReconOnly) {
  $argsList += @("--phases", "recon")
}

if ($DryRun) {
  $argsList += @("--dry-run")
} else {
  # Typer default is dry-run=true; explicitly disable when not requested
  $argsList += @("--no-dry-run")
}

if ($rpcUrl) {
  $argsList += @("--rpc-url", $rpcUrl)
}

if ($blockNumber) {
  $argsList += @("--block-number", $blockNumber)
}

if ($KillSwitchFile) {
  $argsList += @("--kill-switch-file", $KillSwitchFile)
}

Write-Host "Running: $($argsList -join ' ')" -ForegroundColor Cyan
& $argsList[0] $argsList[1..($argsList.Count - 1)]
