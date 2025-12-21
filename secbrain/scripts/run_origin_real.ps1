Param(
    [string]$WorkspaceName = "run-$((Get-Date).ToString('yyyyMMdd-HHmmss'))",
    [string]$RpcUrl,
    [int]$BlockNumber = 19500000,
    [int]$ExploitIterations = 3,
    [double]$ProfitThreshold = 0.1
)

if (-not $RpcUrl) {
    Write-Error "RpcUrl is required. Example: https://mainnet.infura.io/v3/xxx"
    exit 1
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$scope = Join-Path $repoRoot "secbrain/examples/originprotocol/scope.yaml"
$program = Join-Path $repoRoot "secbrain/examples/originprotocol/program.json"
$workspace = Join-Path $repoRoot "targets/originprotocol/runs/$WorkspaceName"

New-Item -ItemType Directory -Force -Path $workspace | Out-Null

Write-Host "Starting SecBrain Origin end-to-end run" -ForegroundColor Cyan
Write-Host "Workspace: $workspace"
Write-Host "RPC: $RpcUrl"
Write-Host "Block: $BlockNumber"

python -m secbrain.cli.secbrain_cli run `
  --scope $scope `
  --program $program `
  --workspace $workspace `
  --no-dry-run `
  --auto-approve `
  --approval-mode auto `
  --phases ingest,plan,recon,hypothesis,exploit,triage,report `
  --rpc-url $RpcUrl `
  --block-number $BlockNumber `
  --exploit-iterations $ExploitIterations `
  --profit-threshold $ProfitThreshold
