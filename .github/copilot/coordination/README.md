# Parallel Agent Coordination System

This directory contains the infrastructure for coordinating multiple GitHub Copilot agents working in parallel on the same pull request.

## Overview

The parallel agent system enables multiple specialized agents to work simultaneously on different aspects of a PR, communicating through a shared coordination state file.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Coordination State File                      │
│              (.github/copilot/coordination/)                 │
│                                                               │
│  - Task assignments and status                               │
│  - Agent states and dependencies                             │
│  - Communication messages                                    │
│  - Progress tracking                                         │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼────┐        ┌────▼────┐       ┌────▼────┐
    │ Agent 1 │        │ Agent 2 │       │ Agent N │
    │ (Test)  │        │ (Review)│       │ (Docs)  │
    └─────────┘        └─────────┘       └─────────┘
```

## Agent Types

### 1. Test Optimizer Agent
- **Role**: Create and run tests for new code
- **Tasks**: 
  - Unit test creation
  - Integration test creation
  - Coverage analysis
  - Test execution
- **Output**: Test suite with >85% coverage

### 2. Code Review Agent
- **Role**: Fix code quality issues
- **Tasks**:
  - Fix type errors
  - Address linting issues
  - Reduce complexity
  - Security review
- **Dependencies**: Waits for Test Optimizer
- **Output**: Clean code passing all quality checks

### 3. Documentation Agent (Future)
- **Role**: Update documentation
- **Tasks**:
  - API documentation
  - Usage examples
  - README updates

## Coordination Protocol

### State File Format

The coordination state file (`pr117_state.json`) contains:

```json
{
  "pr_number": 117,
  "status": "in_progress",
  "agents": {
    "agent_id": {
      "status": "ready|in_progress|completed|failed",
      "tasks_claimed": [],
      "tasks_completed": [],
      "outputs": {}
    }
  },
  "tasks": {
    "task_id": {
      "status": "pending|in_progress|completed|failed",
      "assigned_to": "agent_id",
      "priority": 1,
      "depends_on": []
    }
  },
  "communication": {
    "messages": []
  }
}
```

### Communication Flow

1. **Task Claiming**: Agent reads state, claims unclaimed tasks
2. **Status Updates**: Agent updates state with progress
3. **Dependencies**: Agent waits for dependencies to complete
4. **Completion**: Agent marks tasks complete, signals next agent

### Conflict Resolution

- **Atomic Updates**: Each agent update includes timestamp
- **Priority**: Higher priority agents take precedence
- **Retry Logic**: Failed claims are retried with exponential backoff

## Usage

### Manual Invocation

```bash
# Invoke test optimizer agent
gh copilot task .github/copilot/tasks/pr117-test-optimization.yml

# Invoke code review agent (waits for test optimizer)
gh copilot task .github/copilot/tasks/pr117-code-review.yml
```

### Automated Invocation

Add to PR workflow:
```yaml
- name: Run parallel agents
  run: |
    gh copilot task .github/copilot/tasks/pr117-test-optimization.yml &
    gh copilot task .github/copilot/tasks/pr117-code-review.yml &
    wait
```

## Monitoring

### Check Agent Status

```bash
# View coordination state
cat .github/copilot/coordination/pr117_state.json | jq '.agents'

# View task progress
cat .github/copilot/coordination/pr117_state.json | jq '.progress'
```

### View Agent Logs

Check the GitHub Actions logs for each agent task execution.

## Benefits

1. **Speed**: Parallel execution reduces total time
2. **Specialization**: Each agent focuses on specific domain
3. **Coordination**: Agents avoid conflicts through shared state
4. **Visibility**: Clear progress tracking and status
5. **Scalability**: Easy to add more agents

## Limitations

1. **Dependencies**: Some tasks must run sequentially
2. **Resource Limits**: GitHub has concurrency limits
3. **State Conflicts**: Rare but possible with simultaneous updates

## Best Practices

1. **Clear Task Boundaries**: Define non-overlapping tasks
2. **Explicit Dependencies**: Document what depends on what
3. **Atomic Operations**: Make state updates atomic
4. **Error Handling**: Agents should handle failures gracefully
5. **Status Updates**: Update state frequently for visibility

## Example: PR 117 Workflow

```
Time 0:00 - Test Optimizer starts
  ├── Claims: test_threshold_network_patterns
  ├── Claims: test_immunefi_intelligence_integration
  ├── Claims: test_hypothesis_enhancement
  └── Claims: test_cross_chain_vulnerability_detection

Time 0:30 - Test Optimizer completes testing
  └── Updates state: tests_created=45, coverage=92%

Time 0:31 - Code Review Agent starts (dependency satisfied)
  ├── Claims: fix_mypy_type_errors
  ├── Claims: fix_pylint_issues
  ├── Claims: optimize_complexity
  └── Claims: review_security_patterns

Time 1:15 - Code Review Agent completes
  └── Updates state: type_errors_fixed=145, pylint_score=9.1

Total Time: 1:15 (vs. 2:30 sequential)
Speedup: ~2x
```

## Troubleshooting

### Agent Not Starting

**Problem**: Agent shows "waiting" status indefinitely

**Solutions**:
1. Check dependency agent completed successfully
2. Verify coordination state file is accessible
3. Check for errors in dependency agent logs

### State File Conflicts

**Problem**: Multiple agents updating state simultaneously

**Solutions**:
1. Implement file locking mechanism
2. Use git-based coordination with merge commits
3. Add retry logic with exponential backoff

### Task Dependencies Not Respected

**Problem**: Agent starts before dependencies complete

**Solutions**:
1. Verify dependency checking logic
2. Add explicit wait conditions
3. Use event-based triggers instead of polling

## Future Enhancements

1. **Dynamic Task Assignment**: Auto-assign tasks based on agent load
2. **Agent Pool**: Maintain pool of ready agents
3. **Load Balancing**: Distribute work evenly across agents
4. **Failure Recovery**: Auto-restart failed agents
5. **Metrics Dashboard**: Real-time visualization of progress
