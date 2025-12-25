# Agent Coordination System

This directory contains configuration and state files for coordinating multiple GitHub Copilot agents working in parallel on the same pull request.

## Overview

The agent coordination system enables multiple specialized agents to work together on complex tasks by:
- **Communication**: Shared state file for inter-agent messaging
- **Handoffs**: Structured data passing between agents
- **Dependencies**: Ensuring work happens in the right order
- **Conflict Resolution**: Managing concurrent file modifications
- **Progress Tracking**: Real-time visibility into agent activities

## Active Coordination Sessions

### PR 117 - Threshold Network Optimization

**Status**: Active  
**Agents**: 2 (Security Pattern Agent + Testing Validation Agent)  
**Mode**: Parallel with dependency management

**Files**:
- Configuration: `pr117-coordination.yml`
- Shared State: `pr117-state.json`
- Documentation: `README-PR117.md`
- Quick Start: `QUICKSTART-PR117.md`

**Quick Start**:
```bash
# See quick start guide
cat .github/copilot/agents/QUICKSTART-PR117.md
```

## Directory Structure

```
.github/copilot/agents/
├── README.md                      # This file
├── pr117-coordination.yml         # PR 117 coordination config
├── pr117-state.json              # PR 117 shared state
├── README-PR117.md               # PR 117 detailed documentation
└── QUICKSTART-PR117.md           # PR 117 quick start guide
```

## How Agent Coordination Works

### 1. Configuration (`*-coordination.yml`)
Defines:
- Which agents participate
- Their roles and responsibilities
- Communication protocols
- Workflow phases
- Success criteria

### 2. Shared State (`*-state.json`)
Contains:
- Current status of each agent
- Progress tracking
- Communication log
- Handoff messages
- Artifacts produced
- Blockers and issues

### 3. Task Definitions (`../tasks/*-*.yml`)
Specify:
- Step-by-step instructions for each agent
- When to update shared state
- How to handle handoffs
- Success criteria
- Error handling

## Communication Protocol

### Status Updates
Agents update their status after each major task:
```json
{
  "agent_id": "agent-name",
  "status": "in_progress",
  "progress": 50,
  "message": "Completed task X"
}
```

### Handoffs
When one agent completes work needed by another:
```json
{
  "from_agent": "agent-a",
  "to_agent": "agent-b",
  "handoff_type": "files_ready",
  "data": {
    "modified_files": [...],
    "next_steps": [...]
  }
}
```

### Dependency Management
Agents can wait for others to complete:
```yaml
dependencies:
  - other-agent-id
```

## Creating New Coordination Sessions

To set up parallel agents for a new PR:

### Step 1: Create Coordination Config
```yaml
# .github/copilot/agents/prXXX-coordination.yml
coordination:
  pull_request: XXX
  branch: feature-branch-name
  state_file: .github/copilot/agents/prXXX-state.json

agents:
  - id: agent-1
    role: specialist_type
    responsibilities: [...]
  - id: agent-2
    role: another_specialist
    dependencies: [agent-1]
```

### Step 2: Create Initial State File
```json
{
  "coordination_session": {
    "id": "prXXX-session-001",
    "pull_request": XXX,
    "status": "initialized"
  },
  "agents": {
    "agent-1": {"status": "ready"},
    "agent-2": {"status": "ready"}
  }
}
```

### Step 3: Create Task Definitions
```yaml
# .github/copilot/tasks/prXXX-agent1-task.yml
name: Agent 1 Task
metadata:
  coordination_file: agents/prXXX-coordination.yml
task:
  steps:
    - name: Update state
      action: update_coordination_state
    # ... more steps
```

### Step 4: Document Usage
Create README and quick start guide explaining:
- What problem the agents solve
- How to invoke them
- Expected timeline
- How to monitor progress

## Best Practices

### 1. Clear Separation of Concerns
Each agent should have a distinct, non-overlapping responsibility.

### 2. Explicit Dependencies
If agent B needs agent A's output, declare it explicitly.

### 3. Regular State Updates
Update shared state after each significant task completion.

### 4. Meaningful Messages
Include context in status messages for debugging.

### 5. Conflict Prevention
- Minimize concurrent file edits
- Use clear file ownership
- Log all modifications

### 6. Error Handling
- Set timeouts for waiting agents
- Provide fallback strategies
- Log all errors to shared state

## Monitoring & Debugging

### Check Overall Status
```bash
cat .github/copilot/agents/prXXX-state.json | jq '.coordination_session'
```

### Check Agent Status
```bash
cat .github/copilot/agents/prXXX-state.json | jq '.agents."agent-id"'
```

### View Communication Log
```bash
cat .github/copilot/agents/prXXX-state.json | jq '.communication_log'
```

### Check for Blockers
```bash
cat .github/copilot/agents/prXXX-state.json | jq '.agents[] | select(.blocked == true)'
```

### Validate State File
```bash
cat .github/copilot/agents/prXXX-state.json | jq '.' > /dev/null && echo "Valid JSON" || echo "Invalid JSON"
```

## Common Issues

### Issue: Agent not responding
**Cause**: Task file path incorrect or agent can't read config  
**Fix**: Verify paths in coordination config

### Issue: State file not updating
**Cause**: Permission issues or JSON syntax error  
**Fix**: Check permissions and validate JSON

### Issue: Agents not coordinating
**Cause**: Different state files or missing handoff  
**Fix**: Verify all agents reference same state file

### Issue: Dependency deadlock
**Cause**: Circular dependencies  
**Fix**: Review dependency graph, remove cycles

## Metrics

Track these metrics for each coordination session:

- **Time Savings**: Parallel time vs sequential time
- **Communication Overhead**: Number of state updates
- **Conflict Rate**: Concurrent edit conflicts
- **Success Rate**: Completed vs failed sessions
- **Handoff Efficiency**: Time from handoff creation to receipt

## Future Enhancements

Planned improvements:
1. Real-time dashboard for agent monitoring
2. Automated conflict resolution
3. Agent-to-agent chat interface
4. Dynamic task reallocation
5. Multi-PR coordination support

## Examples

### Example 1: PR 117 (Current)
- **Agents**: Security Pattern Agent + Testing Agent
- **Mode**: Sequential handoff with parallel preparation
- **Time Savings**: ~40% vs sequential

### Example 2: Documentation Update (Hypothetical)
- **Agents**: Content Writer + Technical Reviewer
- **Mode**: Parallel with sync points
- **Time Savings**: ~50% vs sequential

## Getting Help

For questions or issues:
1. Check the specific PR documentation (e.g., README-PR117.md)
2. Review the quick start guide
3. Examine the state file for errors
4. Open an issue with tag `agent-coordination`

## Contributing

When creating new coordination sessions:
1. Follow the naming convention: `prXXX-*`
2. Document thoroughly
3. Include quick start guide
4. Add metrics tracking
5. Update this README with new example

---

**Coordination enables parallel progress. Use it wisely! 🚀**
