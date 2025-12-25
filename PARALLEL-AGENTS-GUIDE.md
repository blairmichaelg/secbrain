# How to Use Parallel Agents for PR 117

## What Has Been Set Up

A **parallel agent coordination system** has been configured to allow two GitHub Copilot agents to work simultaneously on PR 117 (Optimize bug-finding logic for Threshold Network).

### The Two Agents:

1. **Security Pattern Enhancement Agent** - Adds vulnerability patterns
2. **Testing & Validation Agent** - Creates tests and validates

They communicate through a shared state file and coordinate their work automatically.

## How to Invoke the Agents

### Option 1: Quick Start (Recommended)

Open **TWO separate Copilot Chat sessions** (or terminal windows) and run these commands simultaneously:

#### Chat Session 1 - Security Agent:
```
@workspace Please help me execute the PR 117 Security Pattern Enhancement task.

Read and follow the instructions in:
- Task definition: .github/copilot/tasks/pr117-security-patterns.yml
- Coordination config: .github/copilot/agents/pr117-coordination.yml

Your role is to enhance security patterns by:
1. Adding bridge-specific vulnerability patterns
2. Adding tBTC attack vectors (Bitcoin peg vulnerabilities, wallet registry attacks)
3. Enhancing oracle manipulation detection for cross-chain bridges  
4. Adding governance attack patterns specific to DAO structures

Update the shared state file (.github/copilot/agents/pr117-state.json) after each major task with your progress (25%, 50%, 75%, 100%).

When complete, create a handoff message for the testing agent with details about the patterns you added.
```

#### Chat Session 2 - Testing Agent:
```
@workspace Please help me execute the PR 117 Testing and Validation task.

Read and follow the instructions in:
- Task definition: .github/copilot/tasks/pr117-testing-validation.yml
- Coordination config: .github/copilot/agents/pr117-coordination.yml

Your role is to create tests and validate:
1. Wait for the security-pattern-agent to complete (monitor pr117-state.json)
2. Receive the handoff with pattern details
3. Create comprehensive test suite for new patterns
4. Run integration tests against Threshold Network contracts
5. Validate optimizations and report results

Monitor the security agent's progress in the state file and start preparing your test framework while waiting.
```

### Option 2: Using Copilot Task Commands

If your GitHub Copilot supports task commands:

```bash
# Terminal 1
gh copilot task run pr117-security-patterns

# Terminal 2  
gh copilot task run pr117-testing-validation
```

### Option 3: Manual Step-by-Step

If you prefer to guide the agents manually, see the detailed step-by-step guide in `.github/copilot/agents/README-PR117.md`.

## What to Expect

### Timeline (Estimated 50 minutes total)

```
0-5 min:    Both agents initialize and read configs
5-20 min:   Security agent adds patterns, updates state
20-35 min:  Testing agent creates tests (after handoff)
35-45 min:  Testing agent runs validation
45-50 min:  Both agents complete, update PR checklist
```

### Progress Indicators

You'll see progress through the shared state file:

**Security Agent Progress:**
- 25% - Bridge vulnerability patterns added
- 50% - tBTC attack vectors added
- 75% - Oracle manipulation patterns added
- 100% - Governance patterns added + handoff created

**Testing Agent Progress:**
- 0-20% - Waiting for security agent, preparing framework
- 20% - Bridge tests created
- 40% - tBTC tests created
- 60% - Oracle tests created
- 80% - Governance tests created
- 100% - All tests run and validation complete

## Monitoring the Agents

### Check Overall Status
```bash
cat .github/copilot/agents/pr117-state.json | jq '.'
```

### Check Security Agent Status
```bash
cat .github/copilot/agents/pr117-state.json | jq '.agents."security-pattern-agent"'
```

### Check Testing Agent Status
```bash
cat .github/copilot/agents/pr117-state.json | jq '.agents."testing-validation-agent"'
```

### View Communication Log
```bash
cat .github/copilot/agents/pr117-state.json | jq '.communication_log'
```

### Watch Progress in Real-Time
```bash
watch -n 5 'cat .github/copilot/agents/pr117-state.json | jq ".agents | to_entries | .[] | {agent: .key, status: .value.status, progress: .value.progress}"'
```

## What Files Will Be Modified

### By Security Agent:
- `secbrain/secbrain/agents/threshold_network_patterns.py` - New vulnerability patterns
- `secbrain/secbrain/agents/immunefi_intelligence.py` - Enhanced intelligence

### By Testing Agent:
- `secbrain/tests/test_threshold_bridge_patterns.py` - New test file
- `secbrain/tests/test_tbtc_attack_vectors.py` - New test file
- `secbrain/tests/test_oracle_manipulation.py` - New test file
- `secbrain/tests/test_governance_attacks.py` - New test file

## Success Criteria

The parallel agent work is successful when:

✅ Security agent completes all 4 pattern categories
✅ Testing agent creates comprehensive test suite
✅ Test coverage >= 80% for new code
✅ All tests pass
✅ Integration tests validate against Threshold Network scope
✅ PR 117 checklist items are marked complete
✅ No merge conflicts
✅ Both agents report "completed" status

## Troubleshooting

### Problem: Agents not starting
**Solution**: Make sure you've opened two separate chat sessions or terminals. Each agent needs its own context.

### Problem: Testing agent stuck waiting
**Solution**: Check if security agent has completed and created handoff:
```bash
cat .github/copilot/agents/pr117-state.json | jq '.handoffs'
```

### Problem: State file not updating
**Solution**: Ask the agent to manually update the state:
```
Please update the pr117-state.json file with your current progress.
```

### Problem: Agents conflicting on same file
**Solution**: The security agent should complete first before testing agent starts creating tests. If conflict occurs, check timestamps in state file.

## After Completion

Once both agents report completion:

1. **Review the changes**:
```bash
git status
git diff
```

2. **Run the test suite**:
```bash
cd secbrain
pytest tests/test_threshold_bridge_patterns.py -v
pytest tests/test_tbtc_attack_vectors.py -v
pytest tests/test_oracle_manipulation.py -v
pytest tests/test_governance_attacks.py -v
```

3. **Check test coverage**:
```bash
cd secbrain
pytest tests/ -v --cov=secbrain --cov-report=term-missing
```

4. **Update PR 117**:
- Mark remaining checklist items as complete
- Add summary of changes
- Request code review

5. **Clean up** (optional):
```bash
# The coordination state file can be kept for audit trail
# or archived if desired
```

## Benefits You'll See

### Time Savings
- **Sequential approach**: ~90 minutes
- **Parallel approach**: ~50 minutes
- **Savings**: ~40 minutes (44% faster)

### Quality Improvements
- Each agent specializes in their domain
- Testing happens in parallel with development
- Built-in validation steps
- Communication ensures nothing is missed

### Transparency
- All progress tracked in state file
- Communication logged
- Audit trail of all changes
- Clear handoff of work between agents

## Additional Resources

- **Quick Start Guide**: `.github/copilot/agents/QUICKSTART-PR117.md`
- **Detailed Documentation**: `.github/copilot/agents/README-PR117.md`
- **Architecture Diagram**: `.github/copilot/agents/ARCHITECTURE-PR117.md`
- **Coordination Config**: `.github/copilot/agents/pr117-coordination.yml`
- **Security Task**: `.github/copilot/tasks/pr117-security-patterns.yml`
- **Testing Task**: `.github/copilot/tasks/pr117-testing-validation.yml`

## Questions?

If you have questions about the parallel agent system:
1. Check the documentation files above
2. Review the state file for current status
3. Ask in the PR comments
4. Open a new issue with the `agent-coordination` label

---

**Ready to speed up PR 117? Start both agents now! 🚀**
