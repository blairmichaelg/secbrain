# Example PowerShell script for running SecBrain with proper RPC configuration
#
# This script demonstrates best practices for configuring RPC URLs in PowerShell
# to avoid common pitfalls like environment variable concatenation.
#
# Usage:
#   .\run_example.ps1
#   .\run_example.ps1 -RpcUrl "https://ethereum.publicnode.com"
#   .\run_example.ps1 -BlockNumber 18500000

param(
    [Parameter(Mandatory=$false)]
    [string]$ScopeFile = ".\secbrain\examples\originprotocol\scope.yaml",
    
    [Parameter(Mandatory=$false)]
    [string]$ProgramFile = ".\secbrain\examples\originprotocol\program.json",
    
    [Parameter(Mandatory=$false)]
    [string]$WorkspaceDir = ".\targets\originprotocol",
    
    [Parameter(Mandatory=$false)]
    [string]$RpcUrl = "https://ethereum.publicnode.com",
    
    [Parameter(Mandatory=$false)]
    [int]$BlockNumber = 0  # 0 means use latest block
)

# =============================================================================
# FUNCTIONS
# =============================================================================

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# =============================================================================
# VALIDATION
# =============================================================================

Write-ColorOutput "🔍 Validating configuration..." "Cyan"

# Check if scope file exists
if (-not (Test-Path $ScopeFile)) {
    Write-ColorOutput "❌ Error: Scope file not found: $ScopeFile" "Red"
    exit 1
}

# Check if program file exists
if (-not (Test-Path $ProgramFile)) {
    Write-ColorOutput "❌ Error: Program file not found: $ProgramFile" "Red"
    exit 1
}

# Check if required API keys are set
if (-not $env:TOGETHER_API_KEY -and -not $env:OPENAI_API_KEY) {
    Write-ColorOutput "⚠️  Warning: No API keys found for model providers." "Yellow"
    Write-ColorOutput "   Set TOGETHER_API_KEY or OPENAI_API_KEY environment variable." "Yellow"
    Write-ColorOutput "   Example: `$env:TOGETHER_API_KEY = 'your-key-here'" "Yellow"
    Write-ColorOutput "   Continuing with dry-run mode..." "Yellow"
    Write-Host ""
}

# =============================================================================
# EXECUTION
# =============================================================================

Write-ColorOutput "🚀 Starting SecBrain run..." "Green"
Write-Host "   Scope: $ScopeFile"
Write-Host "   Program: $ProgramFile"
Write-Host "   Workspace: $WorkspaceDir"
Write-Host "   RPC URL: $RpcUrl"
if ($BlockNumber -gt 0) {
    Write-Host "   Block: $BlockNumber"
}
Write-Host ""

# Create workspace directory
New-Item -ItemType Directory -Force -Path $WorkspaceDir | Out-Null

# IMPORTANT: Build command as array to ensure proper quoting
# This prevents PowerShell from interpreting URLs as commands
$cmdArgs = @(
    "run",
    "--scope", $ScopeFile,
    "--program", $ProgramFile,
    "--workspace", $WorkspaceDir,
    "--no-dry-run"
)

# Add RPC URL if specified
# CRITICAL: Use proper quoting to avoid concatenation issues
if ($RpcUrl) {
    $cmdArgs += "--rpc-url"
    $cmdArgs += $RpcUrl  # PowerShell handles quoting automatically in arrays
}

# Add block number if specified
if ($BlockNumber -gt 0) {
    $cmdArgs += "--block-number"
    $cmdArgs += $BlockNumber.ToString()
}

# Execute SecBrain
# Note: Using array splatting (@cmdArgs) ensures proper argument passing
try {
    secbrain @cmdArgs
    $exitCode = $LASTEXITCODE
} catch {
    Write-ColorOutput "❌ Error executing SecBrain: $_" "Red"
    exit 1
}

# =============================================================================
# POST-EXECUTION
# =============================================================================

Write-Host ""
if ($exitCode -eq 0) {
    Write-ColorOutput "✅ SecBrain run completed successfully!" "Green"
} else {
    Write-ColorOutput "⚠️  SecBrain run completed with exit code: $exitCode" "Yellow"
}

Write-Host "📁 Results are in: $WorkspaceDir"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Review findings: Get-ChildItem $WorkspaceDir\findings\"
Write-Host "  2. Check logs: Get-Content $WorkspaceDir\logs\*.jsonl | Select-Object -Last 20"
Write-Host "  3. Generate insights: secbrain insights --workspace $WorkspaceDir"
Write-Host ""

# =============================================================================
# POWERSHELL RPC CONFIGURATION TIPS
# =============================================================================

Write-ColorOutput "💡 PowerShell Tips for RPC Configuration:" "Cyan"
Write-Host ""
Write-Host "Setting environment variables in PowerShell:"
Write-Host '  $env:RPC_URL = "https://ethereum.publicnode.com"'
Write-Host ""
Write-Host "For multiple RPC URLs, use scope.yaml instead:"
Write-Host "  rpc_urls:"
Write-Host '    - "https://ethereum.publicnode.com"'
Write-Host '    - "https://eth.llamarpc.com"'
Write-Host ""
Write-Host "❌ AVOID: Concatenation that PowerShell may misinterpret:"
Write-Host '  $env:RPC_URL = https://eth-mainnet.g.alchemy.com/v2/$API_KEY  # Missing quotes!'
Write-Host ""
Write-Host "✅ CORRECT: Always use quotes:"
Write-Host '  $env:RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/$API_KEY"'
Write-Host ""

exit $exitCode
