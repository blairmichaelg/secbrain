# SecBrain Troubleshooting Guide

This guide covers common issues and their solutions when running SecBrain.

## Table of Contents

- [Dependency Issues](#dependency-issues)
- [Model Provider Issues](#model-provider-issues)
- [RPC Configuration Issues](#rpc-configuration-issues)
- [Foundry/Forge Issues](#foundryforge-issues)
- [Performance Issues](#performance-issues)

## Dependency Issues

### eth-hash Backend Missing

**Symptoms:**
- Hypothesis phase fails with error: `None of these hashing backends are installed: ['pycryptodome', 'pysha3']`
- Run completes with 0 hypotheses generated
- Error appears in logs during address validation

**Cause:**
The `eth-utils` library requires `eth-hash` with a cryptographic backend (either `pycryptodome` or `pysha3`) for address checksumming. This is needed during hypothesis generation to validate and normalize Ethereum contract addresses.

**Solution:**

1. **Install eth-hash with pycryptodome backend:**
   ```bash
   pip install "eth-hash[pycryptodome]"
   ```

2. **Verify the fix:**
   ```bash
   python3 scripts/test_eth_hash_fix.py
   ```
   
   You should see:
   ```
   ✅ All tests passed! eth-hash backend is working correctly.
   ```

3. **Install from updated requirements:**
   ```bash
   cd secbrain
   pip install -r requirements.txt
   ```

**Notes:**
- This dependency is now included in `requirements.in` and `pyproject.toml`
- The fix was added in response to hypothesis generation failures
- See [RUN_ANALYSIS_GUIDANCE.md](../RUN_ANALYSIS_GUIDANCE.md) for detailed analysis

## Model Provider Issues

### Spend Limit Reached Errors

**Symptoms:**
- Logs show `spend_limit_reached` errors during plan, hypothesis, or other phases
- Workflow continues but accuracy suffers
- Cached prompts are reused

**Cause:**
API providers (e.g., Groq, Together AI, OpenAI) have spending limits that can be reached during intensive operations.

**Solutions:**

1. **Switch to a different provider** (recommended for immediate fix):
   
   Edit `secbrain/config/models.yaml` and uncomment one of the alternative configurations:

   ```yaml
   # For OpenAI (requires OPENAI_API_KEY)
   worker:
     provider: openai_compatible
     model: gpt-4-turbo-preview
     base_url: https://api.openai.com/v1
     max_tokens: 4096
     temperature: 0.3
   ```

   ```yaml
   # For local models (no API costs, requires Ollama)
   worker:
     provider: ollama
     model: llama3.1:70b
     base_url: http://localhost:11434
   ```

2. **Increase your provider's spend limit:**
   - For Groq: Visit https://console.groq.com/settings/limits
   - For Together AI: Visit https://api.together.xyz/settings/billing
   - For OpenAI: Visit https://platform.openai.com/account/billing/limits

3. **Use cached responses** (automatic):
   SecBrain automatically caches LLM responses to reduce API calls. Running the same target multiple times will use cached responses.

4. **Reduce the number of phases:**
   ```bash
   secbrain run --scope scope.yaml --program program.json \
     --workspace ./targets/test \
     --phases recon,hypothesis,exploit
   ```

### API Key Not Found

**Symptoms:**
- Errors about missing API keys
- Authentication failures

**Solution:**
Set the required environment variables:

```bash
# For Together AI (default)
export TOGETHER_API_KEY=your_key_here

# For OpenAI
export OPENAI_API_KEY=your_key_here

# For Gemini
export GOOGLE_API_KEY=your_key_here

# For Groq
export GROQ_API_KEY=your_key_here

# For Perplexity research
export PERPLEXITY_API_KEY=your_key_here
```

On Windows (PowerShell):
```powershell
$env:TOGETHER_API_KEY="your_key_here"
$env:PERPLEXITY_API_KEY="your_key_here"
```

## RPC Configuration Issues

### PowerShell RPC URL Concatenation Error

**Symptoms:**
- PowerShell scripts fail when setting RPC URLs
- Error messages about command not found
- RPC_URL and RPC_FALLBACK appear concatenated

**Cause:**
PowerShell treats strings with special characters differently. When setting multiple RPC URLs in environment variables, they can be interpreted as a single command.

**Solution:**

1. **Use quotes properly in PowerShell:**

   ✅ **Correct:**
   ```powershell
   $env:RPC_URL = "https://ethereum.publicnode.com"
   ```

   ❌ **Incorrect:**
   ```powershell
   $env:RPC_URL = https://ethereum.publicnode.com  # Missing quotes
   ```

2. **Use scope.yaml for multiple RPC URLs** (recommended):

   Instead of environment variables, configure RPC URLs in your `scope.yaml`:

   ```yaml
   rpc_urls:
     - "https://ethereum.publicnode.com"
     - "https://eth.llamarpc.com"
     - "https://rpc.ankr.com/eth"
   ```

   SecBrain will automatically try each URL in order until one works.

3. **Pass RPC URL via command line:**

   ```bash
   secbrain run --scope scope.yaml --program program.json \
     --workspace ./targets/test \
     --rpc-url "https://ethereum.publicnode.com"
   ```

   On Windows:
   ```powershell
   secbrain run --scope scope.yaml --program program.json `
     --workspace ./targets/test `
     --rpc-url "https://ethereum.publicnode.com"
   ```

### RPC URL Priority

SecBrain uses RPC URLs in this order:

1. Command-line `--rpc-url` parameter
2. URLs from `scope.yaml` `rpc_urls` list
3. Default fallback (if any)

The system will try each URL until one succeeds.

### Common RPC Providers

Free public RPC endpoints:
```yaml
rpc_urls:
  - "https://ethereum.publicnode.com"          # Public Node
  - "https://eth.llamarpc.com"                 # Llama RPC
  - "https://rpc.ankr.com/eth"                 # Ankr
  - "https://ethereum.blockpi.network/v1/rpc/public"  # BlockPI
```

Paid RPC providers (require API keys):
```yaml
rpc_urls:
  - "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY"    # Alchemy
  - "https://mainnet.infura.io/v3/YOUR_KEY"            # Infura
  - "https://eth-mainnet.blastapi.io/YOUR_KEY"         # Blast
```

## Foundry/Forge Issues

### Forge Not Found

**Symptoms:**
- `forge: command not found`
- Exploit phase fails immediately

**Solution:**
Install Foundry:

```bash
# Install foundryup
curl -L https://foundry.paradigm.xyz | bash

# Install forge, cast, anvil
foundryup
```

Verify installation:
```bash
forge --version
```

### Compilation Errors

**Symptoms:**
- Solidity compilation fails
- Version mismatch errors

**Solution:**

1. **Check Solidity version in scope.yaml:**
   ```yaml
   contracts:
     - name: MyContract
       address: "0x..."
       chain_id: 1
       foundry_profile: "my_profile"
   ```

2. **Update foundry.toml:**
   ```toml
   [profile.default]
   solc_version = "0.8.19"
   ```

3. **Clean build cache:**
   ```bash
   forge clean
   ```

### Forked Test Failures

**Symptoms:**
- Tests fail with "invalid RPC response"
- Network timeout errors

**Solution:**

1. **Use a reliable RPC endpoint** (see RPC Configuration above)

2. **Increase timeout:**
   Add to `foundry.toml`:
   ```toml
   [profile.default]
   timeout = 300000  # 5 minutes in ms
   ```

3. **Pin to a specific block:**
   ```bash
   secbrain run --scope scope.yaml --program program.json \
     --workspace ./targets/test \
     --rpc-url "https://ethereum.publicnode.com" \
     --block-number 18500000
   ```

## Performance Issues

### Slow Hypothesis Generation

**Cause:**
- Model provider latency
- Complex contracts
- Network issues

**Solutions:**

1. **Use faster models:**
   Edit `models.yaml` to use smaller, faster models:
   ```yaml
   worker:
     model: meta-llama/Llama-3.1-8B-Instruct-Turbo
   ```

2. **Reduce max_tokens:**
   ```yaml
   worker:
     max_tokens: 4096  # Down from 16384
   ```

3. **Use local models:**
   Install Ollama and switch to local inference (no network latency).

### Out of Memory Errors

**Symptoms:**
- Python crashes with memory errors
- System becomes unresponsive

**Solutions:**

1. **Reduce parallel exploits:**
   In `scope.yaml`:
   ```yaml
   max_parallel_exploits: 1  # Down from 2
   ```

2. **Limit research calls:**
   In `models.yaml`:
   ```yaml
   research:
     max_calls_per_run: 10     # Down from 20
     max_calls_per_phase: 3    # Down from 5
   ```

3. **Run phases individually:**
   ```bash
   # Run one phase at a time
   secbrain run --phases recon --workspace ./targets/test ...
   secbrain run --phases hypothesis --workspace ./targets/test ...
   ```

## Getting Help

If you encounter an issue not covered here:

1. Check the logs in `workspace/logs/run-*.jsonl`
2. Search existing GitHub issues: https://github.com/blairmichaelg/secbrain/issues
3. Open a new issue with:
   - Full error message
   - Relevant log excerpts
   - Your configuration (models.yaml, scope.yaml)
   - Steps to reproduce

For security-sensitive issues, email the maintainers instead of opening a public issue.
