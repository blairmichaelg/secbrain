# SecBrain Architecture

## Overview

SecBrain is a multi-agent security bounty system designed to automate vulnerability research while maintaining strict safety controls and evidence-based findings. It combines:

- **Multi-agent orchestration** for specialized tasks (recon, hypothesis, exploit, triage, reporting)
- **Verification-first evidence collection** via multi-method exploit verification
- **Human-in-the-loop approvals** with explicit audit trails
- **Advisor model** (Groq Llama 3.3 70B) for critical decision checkpoints
- **Guarded tooling** with ACLs, rate limits, and kill-switch
- **Research integration** (Perplexity) for context and learning

## High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                                │
│                    (secbrain_cli.py)                            │
│              Flags: --approval-mode, --dry-run, etc.            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                          │
│                   (bug_bounty_run.py)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Supervisor Agent                       │   │
│  │  - Phase orchestration (Recon → Hypothesis → Exploit)    │   │
│  │  - ACL/rate limit enforcement                            │   │
│  │  - Kill-switch monitoring                                │   │
│  │  - Human approval checkpoints (HITL)                     │   │
│  │  - Audit trail logging (audit.jsonl)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Agent Layer                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │  Program   │ │  Planner   │ │   Recon    │ │   Vuln     │   │
│  │  Ingest    │ │   Agent    │ │   Agent    │ │ Hypothesis │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │  Exploit   │ │  Static    │ │  Triage    │ │ Reporting  │   │
│  │   Agent    │ │  Analysis  │ │   Agent    │ │   Agent    │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│  ┌────────────┐                                                 │
│  │   Meta     │                                                 │
│  │ Learning   │                                                 │
│  └────────────┘                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Verification & Evidence Layer                   │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │ VerificationResult │  │  EvidenceBundle    │                │
│  │ (verified, conf)   │  │ (fingerprint, hash │                │
│  └────────────────────┘  │  baseline vs test)  │                │
│  ┌────────────────────┐  └────────────────────┘                │
│  │    Verifiers       │  (ReflectedXSS, SQLError, Naive)        │
│  └────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Models & Approval Layer                            │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │   Worker Models    │  │ ApprovalManager    │                │
│  │  (Groq Llama 3.3)  │  │  (ask/auto/deny)   │                │
│  └────────────────────┘  └────────────────────┘                │
│  ┌────────────────────┐                                        │
│  │   Advisor Model    │  (Groq Llama 3.3,                       │
│  │   (Groq Llama 3.3) │   critical checkpoints)                 │
│  └────────────────────┘                                        │
│  ┌────────────────────┐                                        │
│  │ Research (Perplex) │                                        │
│  └────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Tools & Guarded Access Layer                   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │    HTTP    │ │   Recon    │ │  Scanners  │ │  Storage   │   │
│  │   Client   │ │   CLIs     │ │ (nuclei)   │ │  (SQLite)  │   │
│  │ (approval) │ │(approval)  │ │            │ │            │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│              All subject to ACLs, rate limits                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Core Layer                                │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │    RunContext      │  │     Audit Log      │                │
│  │    (Session)       │  │  (audit.jsonl)     │                │
│  └────────────────────┘  └────────────────────┘                │
│  ┌────────────────────┐                                        │
│  │     Logging        │  (trace_id, approval decisions)        │
│  └────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
```

## Current Implementation Status

### ✅ Already Implemented

#### 1. Verification-First Evidence System

- **`secbrain/core/verification.py`**: Defines `ResponseFingerprint`, `EvidenceBundle`, `VerificationResult` with confidence scoring
- **`secbrain/agents/verifiers.py`**: Multi-method verifiers
  - `ReflectedXSSVerifier`
  - `SQLiErrorVerifier`
  - `NaiveVerifier`
- **`secbrain/agents/exploit_agent.py`**:
  - Collects baseline response
  - Runs payload on test URL
  - Calls appropriate verifier
  - Emits findings with `verified`, `confidence_score`, `evidence` bundle

#### 2. Human-in-the-Loop Approvals + Audit Trail

- **`secbrain/core/approval.py`**: `ApprovalManager` class
  - Modes: `deny` (safe default), `ask` (interactive), `auto` (trusted)
  - CLI flag: `--approval-mode {deny|ask|auto}`
  - Logs all decisions to `audit.jsonl`
- **Tools subject to approval**:
  - `secbrain/tools/http_client.py`
  - `secbrain/tools/recon_cli_wrappers.py`
- **Audit log**: `<workspace>/audit.jsonl`

### ⚠️ Remaining Work (Path to 9/10)

1. **Hierarchical Specialist Routing**
2. **ReAct Reasoning Chains**
3. **Payload Adaptation/Mutation**
4. **Consensus Verification**

## Roadmap to 9/10 Production-Ready

| Phase | Task | Time | Maturity |
|-------|------|------|----------|
| Now | Verification + Approvals + Audit Log | ✓ Done | 8/10 |
| Phase 1 | Specialist Routing (XSS/SQLi/IDOR) | 16h | 8.3/10 |
| Phase 2 | ReAct Reasoning Chains | 12h | 8.6/10 |
| Phase 3 | Payload Adaptation/Mutation | 8h | 8.8/10 |
| Phase 4 | Consensus Verification | 6h | 9.0/10 |

## Performance Targets

| Metric | Current | Target |
|--------|---------|--------|
| False Positive Rate | ~10-20% | <5% |
| Success Rate | Baseline | +30-40% |
| Enterprise Audit Trail | audit.jsonl | audit.jsonl + reasoning chains |

## Key Files

- Orchestration: `secbrain/workflows/bug_bounty_run.py`, `secbrain/cli/secbrain_cli.py`
- Verification: `secbrain/core/verification.py`, `secbrain/agents/verifiers.py`
- Approvals: `secbrain/core/approval.py`
- Exploit: `secbrain/agents/exploit_agent.py`
- Tools: `secbrain/tools/http_client.py`, `secbrain/tools/recon_cli_wrappers.py`
- Core: `secbrain/core/context.py`, `secbrain/core/logging.py`
- Tests: `tests/test_verifiers.py`, `tests/test_approval_flow.py`
