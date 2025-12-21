# SecBrain Operations Guide

## Installation

### Prerequisites

- Python 3.11+
- uv (recommended) or pip
- Foundry/forge (for on-chain exploit phases)

### Install with uv

```bash
cd secbrain
uv sync
```

### Install with pip

```bash
cd secbrain
pip install -e ".[dev]"
```

### Windows note (forge)

- If forge is installed via the Windows installer, run forge commands from PowerShell/CMD (not Git Bash/WSL) or add `C:\Users\<you>\.foundry\bin` to the shell PATH.

## Configuration

### Environment Variables

Create a `.env` file or export these variables:

```bash
# Required: worker/advisor (Groq)
GROQ_API_KEY=gsk_xxxxxxxxxxxx

# Required: research (Perplexity)
PERPLEXITY_API_KEY=pplx_xxxxxxxxxxxx

# Optional: OpenAI-compatible fallback workers
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxx
```

### Model Configuration

Edit `config/models.yaml`:

```yaml
worker:
  provider: groq
  model: llama-3.3-70b-versatile
  base_url: https://api.groq.com/openai/v1
  max_tokens: 2000
  temperature: 0.3
  top_p: 0.95

advisor:
  provider: groq
  model: llama-3.3-70b-versatile
  base_url: https://api.groq.com/openai/v1
  max_tokens: 1500
  temperature: 0.7
  top_p: 0.95

research:
  provider: perplexity
  model: sonar
  max_calls_per_run: 20
  max_calls_per_phase: 5
```

### Tool Configuration

Edit `config/tools.yaml`:

```yaml
http_client:
  timeout: 30
  max_redirects: 5
  allowed_methods: [GET, POST, PUT, HEAD, OPTIONS]
  require_approval: [DELETE, PATCH]
  rate_limit:
    requests_per_minute: 60
    burst: 10

recon:
  subfinder:
    path: /usr/bin/subfinder
    timeout: 300
    max_domains: 100
  
  amass:
    path: /usr/bin/amass
    timeout: 600
    passive_only: true
  
  httpx:
    path: /usr/bin/httpx
    timeout: 300
    concurrency: 50

scanners:
  nuclei:
    path: /usr/bin/nuclei
    templates_path: ~/nuclei-templates
    allowed_severities: [critical, high, medium]
    blocked_tags: [dos, intrusive]
    require_approval: true
    rate_limit: 100

storage:
  backend: sqlite
  path: workspace/secbrain.db
```

## Running SecBrain

`secbrain run` requires `--scope`, `--program`, and `--workspace`. Running with only `--dry-run` will exit with an error.

### Basic Run

```bash
secbrain run \
  --scope examples/dummy_target/scope.yaml \
  --program examples/dummy_target/program.json \
  --workspace ./targets/example
```

### Dry Run (No Real Requests)

```bash
secbrain run \
  --scope examples/dummy_target/scope.yaml \
  --program examples/dummy_target/program.json \
  --workspace ./targets/example \
  --dry-run
```

### Specific Phases Only

```bash
secbrain run \
  --scope examples/dummy_target/scope.yaml \
  --program examples/dummy_target/program.json \
  --workspace ./targets/example \
  --phases recon,hypothesis
```

### With Kill-Switch

```bash
secbrain run \
  --scope examples/dummy_target/scope.yaml \
  --program examples/dummy_target/program.json \
  --workspace ./targets/example \
  --kill-switch-file ./stop.flag

# In another terminal, to stop:
touch ./stop.flag
```

### Mainnet-Forked Exploit Run

```bash
secbrain run \
  --scope path/to/scope.yaml \
  --program path/to/program.json \
  --workspace ./targets/mainnet \
  --rpc-url https://mainnet.infura.io/v3/<key> \
  --block-number 12345678 \
  --chain-id 1 \
  --exploit-iterations 3 \
  --profit-threshold 0.1 \
  --no-dry-run
```

Key behaviors:

- Recon extracts contract ABI and function signatures from Foundry build artifacts and attaches to assets for hypothesis generation.
- Exploit phase runs iterative forge tests with injected attack bodies; stops early once `profit_threshold` (ETH) is met (forked runs).
- Economic gating in triage marks findings ready_for_report only when decision is PURSUE.
- Meta metrics are appended to `workspace/meta_metrics.jsonl` per run.

### Local Foundry project (no RPC URL)

If you have a local Foundry project (e.g. Damn Vulnerable DeFi / Ethernaut solution repos), you can run the full pipeline without `--rpc-url`. SecBrain will still:

- Compile in Recon using the contract's `foundry_profile`
- Generate hypotheses with concrete function signatures
- Run `forge test` in the Foundry project with the generated test harness under `test/secbrain/`

### Minimal contract scope.yaml

```yaml
contracts:
  - name: MyContract
    address: "0x0000000000000000000000000000000000000000"
    chain_id: 1
    foundry_profile: "default"
    verified: true

domains: []
ips: []
urls: []
excluded_paths: []
allowed_methods: [GET, POST, PUT, HEAD, OPTIONS]
notes: "Contract-only smoke run"
foundry_root: C:\\path\\to\\your\\foundry\\project
max_requests_per_second: 10
respect_robots_txt: true
```

`foundry_root` must point to the top-level Foundry project directory (the folder that contains `foundry.toml`, `src/`, and `test/`). It is not per-contract.

### Minimal program.json

```json
{
  "name": "Local Contract Smoke",
  "platform": "local",
  "rules": ["Only test authorized targets"],
  "focus_areas": ["Smart contracts"],
  "notes": "Local fork validation"
}
```

## Workspace Structure

After a run, the workspace contains:

```text
workspace/
├── logs/
│   └── run-2024-01-15T10-30-00.jsonl
├── recon/
│   ├── subdomains.json
│   ├── endpoints.json
│   └── technologies.json
├── hypotheses/
│   └── vulns.json
├── phases/
│   ├── recon.json
│   ├── hypothesis.json
│   ├── exploit.json
│   └── triage.json
├── exploit_attempts/
│   └── attempt-*/
│       ├── Exploit.t.sol
│       └── forge-output.json
├── findings/
│   ├── confirmed.json
│   └── potential.json
├── reports/
│   └── draft-report.md
├── run_summary.json
└── meta_metrics.jsonl
└── secbrain.db
```

## Post-run validation checklist

1. **Recon ABI/function extraction**

   Open `workspace/phases/recon.json` and confirm each contract asset includes:

   - `metadata.abi`
   - `metadata.functions`

2. **Hypotheses have concrete targets**

   Open `workspace/phases/hypothesis.json` and confirm:

   - `data.missing_targets.missing_contract_or_function` is low
   - Each top hypothesis includes `contract_address` and `function_signature`
   - For Foundry targets, hypotheses include `foundry_profile` (used as `FOUNDRY_PROFILE` during `forge test`)

3. **Exploit loop generated artifacts**

   Open `workspace/phases/exploit.json` and confirm:

   - `data.attempts_count > 0`
   - `data.attempts` entries have `attempt_index`, and `profit_eth` when successful

Inspect `workspace/exploit_attempts/**/Exploit.t.sol` and confirm the injected `attack_body` is non-empty.

For Foundry runs, also confirm the test harness was written into your Foundry project:

- `<foundry_root>/test/secbrain/SecBrainExploit_<hyp_id>_<attempt>.t.sol`

and that each attempt directory includes:

- `stdout.txt`
- `forge-output.json`
- `result.json`

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=secbrain --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_agents.py
```

## Dry Run Testing

Always test new configurations with dry-run:

```bash
secbrain run --scope scope.yaml --program program.json --workspace ./test --dry-run
```

Verify:

1. Logs are created in `workspace/logs/`
2. Agents are invoked in correct order
3. No real network calls are made
4. Configuration is parsed correctly

## Adding New Tools

1. Create wrapper in `secbrain/tools/`:

```python
# secbrain/tools/my_tool.py
from secbrain.core.context import RunContext

async def run_my_tool(
    run_context: RunContext,
    target: str,
    **kwargs
) -> dict:
    # Check kill-switch
    if run_context.is_killed():
        raise RuntimeError("Kill-switch activated")
    
    # Check ACL
    run_context.check_tool_acl("my_tool")
    
    # Check rate limit
    await run_context.acquire_rate_limit("my_tool")
    
    # Execute tool
    # ...
    
    # Log action
    run_context.log_tool_action("my_tool", target, result)
    
    return result
```

2. Add configuration to `config/tools.yaml`

3. Register in tool registry

4. Test with dry-run

## Troubleshooting

### "Kill-switch activated"

The run was stopped by external signal. Check the kill-switch file or internal error threshold.

### "Rate limit exceeded"

Reduce concurrency or increase rate limits in `config/tools.yaml`.

### "Scope violation"

The action target is not in scope.yaml. Review and update scope if needed.

### "Tool not found"

Check tool paths in `config/tools.yaml` and ensure tools are installed.

### "API key not set"

Set required environment variables for Groq (worker/advisor) and Perplexity (research).

## Security Best Practices

- **Never commit API keys** - Use environment variables
- **Review scope carefully** - Ensure targets are in authorized scope
- **Start with dry-run** - Validate before real execution
- **Monitor logs** - Watch for anomalies during runs
- **Use kill-switch** - Be ready to stop at any time
- **Review findings** - Human verification before submission
