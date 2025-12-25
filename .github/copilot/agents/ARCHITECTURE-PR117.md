# PR 117 Agent Coordination Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PR 117 Coordination System                   │
│                                                                       │
│  ┌────────────────────┐           ┌────────────────────┐            │
│  │   Configuration    │           │   Shared State     │            │
│  │                    │           │                    │            │
│  │ pr117-coordination │◄─────────►│  pr117-state.json  │            │
│  │      .yml          │  defines  │                    │            │
│  │                    │           │  - Agent statuses  │            │
│  │ - Agents           │           │  - Progress        │            │
│  │ - Workflow         │           │  - Messages        │            │
│  │ - Protocols        │           │  - Handoffs        │            │
│  └────────────────────┘           └─────────┬──────────┘            │
│                                              │                       │
│                                              │ read/write            │
│                                              │                       │
│  ┌───────────────────────────────────────────┼──────────────────┐   │
│  │                                           │                  │   │
│  │  ┌───────────────────┐          ┌────────▼────────────┐     │   │
│  │  │ Security Pattern  │          │  Testing Validation │     │   │
│  │  │      Agent        │          │       Agent         │     │   │
│  │  │                   │          │                     │     │   │
│  │  │ Task Definition:  │          │  Task Definition:   │     │   │
│  │  │ pr117-security-   │          │  pr117-testing-     │     │   │
│  │  │ patterns.yml      │          │  validation.yml     │     │   │
│  │  │                   │          │                     │     │   │
│  │  │ Responsibilities: │          │  Responsibilities:  │     │   │
│  │  │ ✓ Bridge patterns │          │  ✓ Create tests     │     │   │
│  │  │ ✓ tBTC vectors    │          │  ✓ Run tests        │     │   │
│  │  │ ✓ Oracle patterns │          │  ✓ Validate scope   │     │   │
│  │  │ ✓ Gov patterns    │          │  ✓ Report results   │     │   │
│  │  └─────────┬─────────┘          └──────────┬──────────┘     │   │
│  │            │                               │                 │   │
│  │            │                               │                 │   │
│  │            ▼                               ▼                 │   │
│  │  ┌─────────────────────────────────────────────────┐        │   │
│  │  │            File System / Git Repository         │        │   │
│  │  │                                                  │        │   │
│  │  │  secbrain/secbrain/agents/                      │        │   │
│  │  │  ├── threshold_network_patterns.py ◄────┬───────┤        │   │
│  │  │  ├── immunefi_intelligence.py     ◄────┬┤       │        │   │
│  │  │  └── hypothesis_enhancer.py            ││       │        │   │
│  │  │                                         ││       │        │   │
│  │  │  secbrain/tests/                        ││       │        │   │
│  │  │  ├── test_threshold_bridge_patterns.py ─┼┘       │        │   │
│  │  │  ├── test_tbtc_attack_vectors.py ───────┘        │        │   │
│  │  │  ├── test_oracle_manipulation.py                 │        │   │
│  │  │  └── test_governance_attacks.py                  │        │   │
│  │  └─────────────────────────────────────────────────┘        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Workflow Timeline

```
Time →

Phase 1: INITIALIZATION (0-5 min)
├─ Security Agent:  [Initialize] [Read config] [Update state: ready]
└─ Testing Agent:   [Initialize] [Read config] [Update state: waiting]

Phase 2: PARALLEL EXECUTION (5-35 min)
├─ Security Agent:
│  ├─ [Add bridge patterns]     ──→ State: 25% ──┐
│  ├─ [Add tBTC vectors]        ──→ State: 50%   │
│  ├─ [Add oracle patterns]     ──→ State: 75%   │ Testing Agent
│  └─ [Add governance patterns] ──→ State: 100%  │ monitoring...
│                                                 │
│     [Create handoff message] ─────────────────►┘
│
└─ Testing Agent:
   ├─ [Monitor security agent] ────────────────┐
   ├─ [Prepare test framework] ────────────────┤ Waiting for
   └─ [Wait for handoff] ──────────────────────┘ patterns
      ↓
      [Receive handoff]
      ↓
   ├─ [Create bridge tests]      ──→ State: 20%
   ├─ [Create tBTC tests]        ──→ State: 40%
   ├─ [Create oracle tests]      ──→ State: 60%
   ├─ [Create governance tests]  ──→ State: 80%
   └─ [Run & validate tests]     ──→ State: 100%

Phase 3: VALIDATION (35-45 min)
├─ Testing Agent:  [Run integration tests] [Validate scope] [Report]
└─ Security Agent: [Review results] [Fix issues if needed]

Phase 4: COMPLETION (45-50 min)
└─ Both Agents: [Update PR checklist] [Generate report] [Clean up]
```

## Communication Flow

```
┌──────────────────────┐
│  Security Agent      │
│  (Agent A)           │
└──────────┬───────────┘
           │
           │ 1. Update status
           ▼
   ┌───────────────────┐
   │  pr117-state.json │
   │                   │
   │  {                │
   │    "agents": {    │
   │      "security-   │
   │       pattern":   │
   │       {           │
   │         "status": │
   │         "progress"│
   │         "message" │
   │       }           │
   │    }              │
   │  }                │
   └─────────┬─────────┘
             │
             │ 2. Read status
             ▼
   ┌──────────────────┐
   │  Testing Agent   │
   │  (Agent B)       │
   └──────────────────┘

Handoff Flow:

Security Agent              State File              Testing Agent
     │                          │                         │
     │ ──[ handoff created ]──► │                         │
     │                          │ ◄──[ polling ]────────  │
     │                          │                         │
     │                          │ ──[ handoff data ]────► │
     │                          │                         │
     │                          │ ◄──[ received ]────────  │
     │                          │                         │
     │ ◄──[ ack updated ]─────  │                         │
```

## State Transitions

```
Security Pattern Agent State Machine:

    ┌─────────┐
    │  ready  │
    └────┬────┘
         │ start
         ▼
  ┌──────────────┐
  │ in_progress  │◄────┐
  └──────┬───────┘     │
         │             │ next task
         │ all tasks   │
         │ complete    │
         ▼             │
    ┌─────────┐        │
    │handoff  │────────┘
    └────┬────┘
         │ acknowledged
         ▼
   ┌───────────┐
   │ completed │
   └───────────┘


Testing Validation Agent State Machine:

    ┌─────────┐
    │  ready  │
    └────┬────┘
         │ init
         ▼
    ┌─────────┐
    │ waiting │◄────────────┐
    └────┬────┘             │
         │ handoff received │
         ▼                  │
  ┌──────────────┐          │
  │ in_progress  │──────────┘
  └──────┬───────┘   blocked
         │ tests complete
         ▼
   ┌───────────┐
   │ completed │
   └───────────┘
```

## File Interaction Map

```
Configuration Files              State Files              Output Files
      (Input)                   (Coordination)            (Results)

pr117-coordination.yml ─────┐
                            │
pr117-security-patterns.yml─┼──► pr117-state.json ──┐
                            │          ▲             │
pr117-testing-validation.yml┘          │             │
                                       │             │
                            ┌──────────┴─────┐       │
                            │                │       │
                            │   read/write   │       │
                            │                │       │
                            └────────────────┘       │
                                                     │
                                                     ▼
                            Modified Python Files:
                            • threshold_network_patterns.py
                            • immunefi_intelligence.py
                            
                            New Test Files:
                            • test_threshold_bridge_patterns.py
                            • test_tbtc_attack_vectors.py
                            • test_oracle_manipulation.py
                            • test_governance_attacks.py
```

## Data Flow During Handoff

```
Step 1: Security Agent Completes Work
┌─────────────────────────────────┐
│ Security Agent                  │
│                                 │
│ Files Modified:                 │
│ ✓ threshold_network_patterns.py│
│ ✓ immunefi_intelligence.py     │
│                                 │
│ Patterns Added:                 │
│ ✓ bridge_vulnerabilities        │
│ ✓ tbtc_attack_vectors           │
│ ✓ oracle_manipulation           │
│ ✓ governance_patterns           │
└────────────┬────────────────────┘
             │
             │ Create handoff object
             ▼
┌──────────────────────────────────────┐
│ Handoff Data Structure               │
│ {                                    │
│   "from": "security-pattern-agent",  │
│   "to": "testing-validation-agent",  │
│   "type": "files_ready",             │
│   "priority": "high",                │
│   "data": {                          │
│     "modified_files": [...],         │
│     "new_patterns": [...],           │
│     "test_scenarios": [...]          │
│   }                                  │
│ }                                    │
└────────────┬─────────────────────────┘
             │
             │ Write to state file
             ▼
┌──────────────────────────────────────┐
│ pr117-state.json                     │
│ {                                    │
│   "handoffs": [                      │
│     { /* handoff object */ }         │
│   ]                                  │
│ }                                    │
└────────────┬─────────────────────────┘
             │
             │ Testing agent polls
             ▼
┌──────────────────────────────────────┐
│ Testing Agent                        │
│                                      │
│ Receives:                            │
│ • List of modified files             │
│ • New pattern definitions            │
│ • Test scenarios to implement        │
│                                      │
│ Actions:                             │
│ • Create test files                  │
│ • Write test cases                   │
│ • Run validation                     │
└──────────────────────────────────────┘
```

## Success Path

```
Start
  │
  ├─ Both agents initialize ─────────────────────────────► ✓
  │
  ├─ Security agent adds patterns ───────────────────────► ✓
  │  └─ State updated 4 times (25%, 50%, 75%, 100%)
  │
  ├─ Handoff created ────────────────────────────────────► ✓
  │  └─ Contains all necessary data
  │
  ├─ Testing agent receives handoff ─────────────────────► ✓
  │  └─ Validates handoff data
  │
  ├─ Testing agent creates tests ────────────────────────► ✓
  │  └─ State updated 5 times (20%, 40%, 60%, 80%, 100%)
  │
  ├─ All tests pass ─────────────────────────────────────► ✓
  │  └─ Coverage >= 80%
  │
  ├─ Validation successful ──────────────────────────────► ✓
  │  └─ Threshold Network scope confirmed
  │
  └─ PR checklist updated ───────────────────────────────► ✓
     └─ All items marked complete
        │
        ▼
     SUCCESS! 🎉
```

---

This architecture enables efficient parallel work while maintaining coordination and quality.
