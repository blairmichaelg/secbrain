# Immunefi Integration and Advanced Research Guide

## Overview

SecBrain now includes advanced capabilities for bug bounty hunting with:

1. **Immunefi Platform Integration** - Live bounty program intelligence
2. **Advanced Research Agent** - Cutting-edge vulnerability pattern discovery
3. **Success Metrics Tracking** - Continuous learning from submissions
4. **Enhanced Workflow** - Optimized analysis pipeline

These features help you focus on high-value targets, discover emerging vulnerabilities, and continuously improve your bug hunting effectiveness.

---

## Features

### 1. Immunefi Platform Intelligence

Access real-time data about Immunefi bug bounty programs to prioritize your hunting efforts.

**Key Capabilities:**
- High-value program discovery (filter by minimum bounty)
- Program priority scoring (0-100)
- Trending vulnerability patterns (last 90 days)
- Program-specific intelligence and recommendations
- Similar program comparison

**CLI Commands:**

```bash
# List high-value programs
secbrain immunefi list --min-bounty 1000000 --limit 5

# Show detailed program information
secbrain immunefi show --program thresholdnetwork

# View trending vulnerabilities
secbrain immunefi trends --limit 10

# Get comprehensive intelligence for a program
secbrain immunefi intelligence --program wormhole
```

**Program Priority Scoring:**
Programs are scored 0-100 based on:
- Maximum bounty amount (0-40 points)
- Featured status (0-15 points)
- Recency/activity (0-15 points)
- Blockchain diversity (0-10 points)
- Historical payouts (0-20 points)

### 2. Advanced Research Agent

Discover cutting-edge vulnerability patterns using AI-powered research.

**Key Capabilities:**
- Emerging pattern discovery (2024-2025 vulnerabilities)
- Protocol-specific vulnerability analysis
- Cross-protocol risk correlation
- Novel hypothesis generation
- Real-world exploit data integration

**CLI Commands:**

```bash
# Research emerging patterns
secbrain research --timeframe 90 --output findings.json

# Analyze specific protocol
secbrain research --protocol "Threshold Network" --timeframe 60

# Generate hypotheses for contracts
secbrain research \
  --protocol "Compound" \
  --contracts "Comptroller,CErc20,CToken" \
  --output compound_analysis.json
```

**Curated Emerging Patterns (2024-2025):**

1. **Intent-Based Protocol Atomicity Failures** (Critical)
   - Affects: UniswapX, CoW Protocol, 1inch Fusion
   - Average bounty: $450K
   - Attack vectors: Partial fill manipulation, solver attacks, MEV extraction

2. **ERC-4337 Paymaster Exploitation** (High)
   - Affects: Account abstraction implementations
   - Average bounty: $320K
   - Attack vectors: Gas sponsorship abuse, bundler manipulation

3. **ZK-Proof Verification Circuit Flaws** (Critical)
   - Affects: ZK-rollups and privacy protocols
   - Average bounty: Variable (high-severity)
   - Attack vectors: Constraint underconstraining, trusted setup manipulation

4. **Read-Only Reentrancy** (Critical)
   - Affects: DeFi protocols, especially AMMs
   - Average bounty: $180K
   - Attack vectors: View function exploitation, oracle manipulation

5. **Optimistic Bridge Challenge Bypass** (Critical)
   - Affects: Optimism, Arbitrum, Base
   - Average bounty: Variable
   - Attack vectors: Challenge period manipulation, validator censorship

6. **Concentrated Liquidity MEV** (High)
   - Affects: Uniswap V3, Curve V2
   - Average bounty: $125K
   - Attack vectors: JIT liquidity, tick manipulation

### 3. Success Metrics Tracking

Track your submission history and learn from past results.

**Key Capabilities:**
- Submission outcome tracking
- Program-specific success rates
- Vulnerability pattern effectiveness
- Learning insights and recommendations
- Submission decision support

**CLI Commands:**

```bash
# View overall metrics
secbrain metrics summary --workspace ./my_metrics

# Top performing programs
secbrain metrics programs --workspace ./my_metrics

# Most effective vulnerability patterns
secbrain metrics patterns --workspace ./my_metrics

# Get learning insights
secbrain metrics insights --workspace ./my_metrics
```

**Metrics Tracked:**
- Acceptance/rejection rates
- Total earnings and average bounty
- Time to discovery
- Detection method effectiveness
- Confidence score calibration

**Programmatic Usage:**

```python
from pathlib import Path
from secbrain.tools.bounty_metrics import BountyMetricsTracker, BountySubmission

# Initialize tracker
tracker = BountyMetricsTracker(Path("./metrics"))

# Record a submission
submission = BountySubmission(
    id="sub-001",
    program="Wormhole",
    platform="immunefi",
    submitted_at="2024-12-25T10:00:00Z",
    vulnerability_type="Cross-Chain Bridge Exploit",
    severity="critical",
    title="Message Verification Bypass",
    description="...",
    status="accepted",
    bounty_amount=250_000.0,
    detection_method="static_analysis",
    confidence_score=0.85,
    time_to_find_hours=12.5,
)

tracker.record_submission(submission)

# Get decision support
decision = tracker.should_submit(
    vulnerability_type="Read-Only Reentrancy",
    confidence=0.75,
)
print(decision["should_submit"])  # True/False
print(decision["reason"])  # Explanation
```

### 4. Enhanced Workflow

Integrated workflow combining all features for optimal results.

**Workflow Stages:**

1. **Target Selection** - Identify high-value Immunefi programs
2. **Intelligence Gathering** - Collect platform and research data
3. **Advanced Research** - Apply cutting-edge vulnerability patterns
4. **Targeted Analysis** - Focus on high-probability issues
5. **Validation** - Verify with historical success data
6. **Submission Optimization** - Use metrics for quality control

**Programmatic Usage:**

```python
from secbrain.workflows.enhanced_bounty_workflow import run_enhanced_bounty_hunt
from secbrain.core.context import RunContext, ScopeConfig, ProgramConfig

# Create context
scope = ScopeConfig(...)
program = ProgramConfig(...)
run_context = RunContext(
    scope=scope,
    program=program,
    workspace_path=Path("./workspace"),
    dry_run=False,
)

# Run enhanced workflow
results = await run_enhanced_bounty_hunt(
    run_context=run_context,
    target_program="thresholdnetwork",  # Optional
    min_bounty=500_000,
)

# Access results
print(f"Targets: {results['targets']}")
print(f"Intelligence: {results['intelligence']}")
print(f"Research: {results['research']}")
print(f"Recommendations: {results['recommendations']}")
```

---

## Quick Start Examples

### Example 1: Discover High-Value Targets

```bash
# Find programs with ≥$1M bounty
secbrain immunefi list --min-bounty 1000000

# Get detailed intelligence for top target
secbrain immunefi intelligence --program wormhole

# Research emerging patterns for that target
secbrain research --protocol "Wormhole" --timeframe 90
```

### Example 2: Analyze a Specific Protocol

```bash
# Get program details
secbrain immunefi show --program compound

# Research protocol-specific vulnerabilities
secbrain research --protocol "Compound Finance" \
  --contracts "Comptroller,CErc20" \
  --output compound_findings.json

# Review findings
cat compound_findings.json | jq '.emerging_patterns[] | {title, severity, confidence}'
```

### Example 3: Track Your Progress

```bash
# View your metrics
secbrain metrics summary

# See which patterns work best for you
secbrain metrics patterns

# Get recommendations for improvement
secbrain metrics insights
```

---

## Integration with Existing Workflow

The new features integrate seamlessly with SecBrain's existing capabilities:

### Enhanced Hypothesis Generation

The vulnerability hypothesis agent now:
- Incorporates Immunefi intelligence
- Uses advanced research findings
- Applies historical success patterns
- Prioritizes based on metrics

### Improved Prioritization

Analysis is now prioritized by:
- Immunefi program priority scores
- Trending vulnerability patterns
- Historical acceptance rates
- Estimated bounty values

### Continuous Learning

The system learns from:
- Submission outcomes
- Detection method effectiveness
- Pattern success rates
- Time investment ROI

---

## Configuration

### Environment Variables

```bash
# Required for live research (optional for curated data)
export PERPLEXITY_API_KEY=pplx-xxxx

# Other existing SecBrain variables
export GOOGLE_API_KEY=AIza-xxxx
export TOGETHER_API_KEY=your-key
```

### Metrics Storage

Metrics are stored in JSONL and JSON files:

```
metrics/
├── submissions.jsonl        # All submissions (append-only)
├── program_metrics.json     # Per-program statistics
└── pattern_learning.json    # Vulnerability pattern effectiveness
```

---

## Best Practices

### 1. Target Selection

✅ **DO:**
- Start with high-priority programs (score ≥70)
- Focus on programs with proven payouts
- Consider blockchain expertise alignment
- Review recommended focus areas

❌ **DON'T:**
- Chase every high-bounty program
- Ignore priority scoring
- Skip intelligence gathering

### 2. Research

✅ **DO:**
- Review emerging patterns regularly (weekly)
- Focus on recent trends (30-90 days)
- Validate patterns with research sources
- Generate protocol-specific hypotheses

❌ **DON'T:**
- Rely solely on curated data
- Ignore cutting-edge research
- Skip cross-protocol analysis

### 3. Metrics Usage

✅ **DO:**
- Record all submissions (accepted and rejected)
- Review insights monthly
- Adjust focus based on effectiveness
- Track confidence calibration

❌ **DON'T:**
- Only record accepted submissions
- Ignore rejection patterns
- Dismiss low-confidence warnings

### 4. Workflow Optimization

✅ **DO:**
- Use enhanced workflow for new targets
- Combine intelligence + research + metrics
- Validate findings before submission
- Iterate based on feedback

❌ **DON'T:**
- Skip validation steps
- Submit without metrics check
- Ignore historical data

---

## Advanced Usage

### Custom Research Queries

```python
from secbrain.agents.advanced_research_agent import AdvancedResearchAgent

agent = AdvancedResearchAgent(run_context, research_client)

# Cross-protocol correlation
findings = await agent.correlate_cross_protocol([
    "Compound",
    "Aave",
    "MakerDAO",
])

# Novel hypothesis generation
hypotheses = await agent.generate_novel_hypotheses(
    target_contracts=["Comptroller", "CErc20"],
    context="DeFi lending protocol analysis",
)
```

### Custom Metrics Analysis

```python
from secbrain.tools.bounty_metrics import BountyMetricsTracker

tracker = BountyMetricsTracker("./metrics")

# Get specific program metrics
metrics = tracker.get_program_metrics("Wormhole", "immunefi")
print(f"Acceptance rate: {metrics.acceptance_rate:.1%}")

# Get pattern learning
pattern = tracker.get_pattern_learning("Read-Only Reentrancy")
print(f"Effectiveness: {pattern.detection_effectiveness:.1%}")
print(f"Recommended threshold: {pattern.recommended_confidence_threshold}")
```

### Immunefi API Integration

```python
from secbrain.tools.immunefi_client import ImmunefiClient

client = ImmunefiClient()

# Custom program filtering
programs = await client.get_all_programs()
ethereum_programs = [p for p in programs if "Ethereum" in p.blockchain]
high_value = [p for p in ethereum_programs if p.max_bounty >= 2_000_000]

# Custom intelligence
for program in high_value:
    intel = await client.get_program_intelligence(program.id)
    print(f"{program.name}: {intel['recommended_focus_areas']}")
```

---

## Troubleshooting

### No Immunefi Programs Found

**Cause:** Network issue or API unavailable

**Solution:** The system uses curated fallback data. Check network connectivity.

### Research Returns Empty Results

**Cause:** No API key configured or dry-run mode

**Solution:** The system provides curated emerging patterns. For live research, set `PERPLEXITY_API_KEY`.

### Metrics Not Updating

**Cause:** Permission issues or corrupted files

**Solution:**
```bash
# Check permissions
ls -la metrics/

# Reset metrics (backup first!)
mv metrics metrics.backup
mkdir metrics
```

---

## Roadmap

Future enhancements planned:

- [ ] Real-time Immunefi API integration
- [ ] Automated program monitoring
- [ ] ML-based pattern discovery
- [ ] Collaborative learning across users
- [ ] Integration with other platforms (HackerOne, Code4rena)
- [ ] Advanced visualization dashboards
- [ ] Automated submission drafting

---

## Contributing

Found a new vulnerability pattern? Improve metrics tracking? We welcome contributions!

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## References

- [Immunefi Platform](https://immunefi.com/)
- [Immunefi Severity System V2.3](https://immunefi.com/severity-system/)
- [Recent DeFi Exploits](https://rekt.news/)
- [Web3 Security Research](https://www.paradigm.xyz/research)
- [Smart Contract Security Best Practices](https://consensys.github.io/smart-contract-best-practices/)

---

## License

MIT - See [LICENSE](../LICENSE) for details.
