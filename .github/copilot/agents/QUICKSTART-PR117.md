# Quick Start: Parallel Agents for PR 117

## 🚀 Get Started in 3 Steps

### Step 1: Invoke Security Pattern Agent

Open a new Copilot Chat session and run:

```
@workspace Please execute the PR 117 Security Pattern Enhancement task. 

Read the task definition from: .github/copilot/tasks/pr117-security-patterns.yml
Follow the coordination protocol in: .github/copilot/agents/pr117-coordination.yml
Update shared state in: .github/copilot/agents/pr117-state.json

Focus on:
1. Adding bridge-specific vulnerability patterns
2. Adding tBTC attack vectors
3. Enhancing oracle manipulation detection
4. Adding governance attack patterns

After each major task, update the shared state file with your progress.
```

### Step 2: Invoke Testing Validation Agent (In Parallel)

Open a **second** Copilot Chat session and run:

```
@workspace Please execute the PR 117 Testing and Validation task.

Read the task definition from: .github/copilot/tasks/pr117-testing-validation.yml
Follow the coordination protocol in: .github/copilot/agents/pr117-coordination.yml
Monitor shared state in: .github/copilot/agents/pr117-state.json

Wait for the security-pattern-agent to complete, then:
1. Receive handoff from security agent
2. Create comprehensive test suite
3. Run integration tests
4. Validate against Threshold Network scope
5. Report results in shared state

Monitor the security agent's progress and start preparing tests as patterns become available.
```

### Step 3: Monitor Progress

Check progress anytime:

```bash
# View overall status
cat .github/copilot/agents/pr117-state.json | jq '.agents'

# Check security agent progress
cat .github/copilot/agents/pr117-state.json | jq '.agents."security-pattern-agent"'

# Check testing agent progress
cat .github/copilot/agents/pr117-state.json | jq '.agents."testing-validation-agent"'

# View communication log
cat .github/copilot/agents/pr117-state.json | jq '.communication_log'
```

## 📊 Expected Timeline

- **Minutes 0-5**: Initialization & setup
- **Minutes 5-20**: Security agent adds patterns
- **Minutes 20-35**: Testing agent creates tests (starts when patterns are ready)
- **Minutes 35-45**: Integration testing & validation
- **Minutes 45-50**: Completion & reporting

**Total**: ~50 minutes (vs 90+ minutes sequential)

## ✅ Success Indicators

You'll know it's working when:

1. ✅ Both agents update state file regularly
2. ✅ Security agent shows progress: 0% → 25% → 50% → 75% → 100%
3. ✅ Testing agent changes from "waiting" to "in_progress"
4. ✅ Handoff message appears in communication_log
5. ✅ All PR 117 checklist items marked complete

## 🔍 Troubleshooting

### Problem: Agent isn't responding
**Solution**: Verify the agent can read the task file:
```bash
cat .github/copilot/tasks/pr117-security-patterns.yml
cat .github/copilot/tasks/pr117-testing-validation.yml
```

### Problem: State file not updating
**Solution**: Check file permissions:
```bash
ls -la .github/copilot/agents/pr117-state.json
chmod 644 .github/copilot/agents/pr117-state.json
```

### Problem: Agents not communicating
**Solution**: Verify state file is valid JSON:
```bash
cat .github/copilot/agents/pr117-state.json | jq '.'
```

## 📝 What Each Agent Does

### Security Pattern Enhancement Agent
```
Input:  Existing pattern files
        ↓
Task 1: Add bridge vulnerabilities  (25% progress)
        ↓
Task 2: Add tBTC attack vectors    (50% progress)
        ↓
Task 3: Enhance oracle detection   (75% progress)
        ↓
Task 4: Add governance patterns    (100% progress)
        ↓
Output: Enhanced pattern files + Handoff to testing agent
```

### Testing & Validation Agent
```
Input:  Wait for security agent handoff
        ↓
Receive: Modified files + Pattern details
        ↓
Task 1: Create bridge tests         (20% progress)
        ↓
Task 2: Create tBTC tests           (40% progress)
        ↓
Task 3: Create oracle tests         (60% progress)
        ↓
Task 4: Create governance tests     (80% progress)
        ↓
Task 5: Run & validate all tests    (100% progress)
        ↓
Output: Test suite + Validation report
```

## 🎯 Next Steps After Completion

1. Review the changes made by both agents
2. Run the full test suite to verify
3. Update PR 117 description with results
4. Request code review
5. Merge when approved!

## 📚 More Information

- Full documentation: `.github/copilot/agents/README-PR117.md`
- Coordination config: `.github/copilot/agents/pr117-coordination.yml`
- Security task: `.github/copilot/tasks/pr117-security-patterns.yml`
- Testing task: `.github/copilot/tasks/pr117-testing-validation.yml`

## 💡 Pro Tips

1. **Start both agents at the same time** - they coordinate automatically
2. **Monitor the state file** - it's the single source of truth
3. **Check communication_log** - see all inter-agent messages
4. **Trust the handoff** - testing agent waits for security agent
5. **Review the artifacts** - both agents list files they modify

---

**Happy parallel processing! 🚀**
