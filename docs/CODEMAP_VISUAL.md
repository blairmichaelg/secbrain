# SecBrain Visual Codemap

This document provides visual representations of the SecBrain codebase structure.

## Module Dependency Graph

```mermaid
graph TD
    CLI[CLI Layer<br/>3 files, 1K LOC]
    WF[Workflows<br/>8 files, 1.8K LOC]
    AG[Agents<br/>22 files, 11.6K LOC]
    CORE[Core<br/>15 files, 3.2K LOC]
    TOOLS[Tools<br/>12 files, 3.7K LOC]
    MODELS[Models<br/>4 files, 637 LOC]
    UTILS[Utils<br/>6 files, 660 LOC]
    CONFIG[Config<br/>2 files, 59 LOC]
    INSIGHTS[Insights<br/>4 files, 925 LOC]
    
    CLI --> WF
    WF --> AG
    WF --> CORE
    AG --> CORE
    AG --> TOOLS
    AG --> MODELS
    AG --> UTILS
    AG --> CONFIG
    TOOLS --> CORE
    CORE --> MODELS
    CORE --> CONFIG
    CORE --> CLI
    INSIGHTS --> CORE
    
    style CLI fill:#e1f5ff
    style WF fill:#ffe1e1
    style AG fill:#fff3e1
    style CORE fill:#e1ffe1
    style TOOLS fill:#f3e1ff
    style MODELS fill:#ffe1f3
```

## Agent Ecosystem

```mermaid
graph LR
    SUP[Supervisor Agent]
    
    subgraph Intelligence
        REC[Recon Agent]
        VULN[Vuln Hypothesis Agent]
        RES[Research Orchestrator]
        ADV[Advanced Research]
        IMM[Immunefi Intelligence]
        META[Meta Learning]
    end
    
    subgraph Exploitation
        EXP[Exploit Agent]
        SPEC[Exploit Specialists]
        STAT[Static Analysis]
        ORACLE[Oracle Detector]
        VERIFY[Verifiers]
    end
    
    subgraph Processing
        TRIAGE[Triage Agent]
        REP[Reporting Agent]
        PLAN[Planner Agent]
    end
    
    subgraph Knowledge
        PATTERN[Exploit Pattern DB]
        SOL[Solidity Patterns]
        THRESH[Threshold Patterns]
        ENH[Hypothesis Enhancer]
        INGEST[Program Ingest]
    end
    
    SUP --> Intelligence
    SUP --> Exploitation
    SUP --> Processing
    
    Intelligence -.-> Knowledge
    Exploitation -.-> Knowledge
    
    style SUP fill:#ff9999
    style Intelligence fill:#99ccff
    style Exploitation fill:#ffcc99
    style Processing fill:#99ff99
    style Knowledge fill:#cc99ff
```

## Workflow State Machine

```mermaid
stateDiagram-v2
    [*] --> Init
    Init --> Recon: Start Bounty Hunt
    
    Recon --> Hypothesis: Targets Found
    Recon --> Complete: No Targets
    
    Hypothesis --> Research: Hypotheses Generated
    Hypothesis --> Complete: No Viable Hypotheses
    
    Research --> Exploit: Research Complete
    
    Exploit --> Verification: Exploit Developed
    Exploit --> Hypothesis: Exploit Failed
    
    Verification --> Triage: Exploit Verified
    Verification --> Exploit: Verification Failed
    
    Triage --> Reporting: Findings Validated
    Triage --> Complete: No Valid Findings
    
    Reporting --> Complete: Report Generated
    
    Complete --> [*]
    
    state Recon {
        [*] --> SubdomainEnum
        SubdomainEnum --> PortScan
        PortScan --> ServiceDetect
        ServiceDetect --> [*]
    }
    
    state Hypothesis {
        [*] --> PatternMatch
        PatternMatch --> AIGeneration
        AIGeneration --> Enhancement
        Enhancement --> [*]
    }
    
    state Exploit {
        [*] --> PayloadGen
        PayloadGen --> StaticTest
        StaticTest --> DynamicTest
        DynamicTest --> [*]
    }
```

## Data Flow Architecture

```mermaid
flowchart TB
    subgraph External
        USER[User CLI Input]
        PERP[Perplexity API]
        IMF[Immunefi API]
        TOOLS_EXT[External Tools:<br/>subfinder, amass, foundry]
    end
    
    subgraph SecBrain
        CLI_LAYER[CLI Layer]
        
        subgraph Workflows
            WORKFLOW[Bug Bounty Workflow]
            CHECKPOINT[Checkpoint Manager]
            PARALLEL[Parallel Executor]
        end
        
        subgraph Agents
            SUPERVISOR[Supervisor]
            AGENT_POOL[Agent Pool<br/>22 Agents]
        end
        
        subgraph Core
            CTX[Context Manager]
            VAL[Validator]
            LOG[Logger]
            APPROVE[Approval System]
        end
        
        subgraph Storage
            FS[File System<br/>Workspace]
            DB[(SQLite<br/>Metrics DB)]
            CACHE[Cache Layer]
        end
        
        subgraph Models
            LLM[LLM Abstraction]
            GEMINI[Gemini Advisor]
        end
    end
    
    USER --> CLI_LAYER
    CLI_LAYER --> WORKFLOW
    WORKFLOW --> SUPERVISOR
    SUPERVISOR --> AGENT_POOL
    AGENT_POOL --> CTX
    AGENT_POOL --> TOOLS_EXT
    AGENT_POOL --> PERP
    AGENT_POOL --> IMF
    AGENT_POOL --> LLM
    LLM --> GEMINI
    CTX --> VAL
    CTX --> LOG
    CTX --> APPROVE
    SUPERVISOR --> CHECKPOINT
    SUPERVISOR --> PARALLEL
    AGENT_POOL --> FS
    AGENT_POOL --> DB
    AGENT_POOL --> CACHE
    
    style USER fill:#e1f5ff
    style PERP fill:#ffe1e1
    style IMF fill:#ffe1e1
    style TOOLS_EXT fill:#ffe1e1
    style SUPERVISOR fill:#ff9999
    style DB fill:#99ff99
```

## Component Interaction Sequence

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Workflow
    participant Supervisor
    participant ReconAgent
    participant HypothesisAgent
    participant ExploitAgent
    participant TriageAgent
    participant ReportingAgent
    participant Approval
    participant Storage
    
    User->>CLI: secbrain run
    CLI->>Workflow: Initialize
    Workflow->>Supervisor: Start bounty hunt
    
    Supervisor->>ReconAgent: Run recon
    ReconAgent->>Storage: Save targets
    ReconAgent-->>Supervisor: Targets found
    
    Supervisor->>HypothesisAgent: Generate hypotheses
    HypothesisAgent->>Storage: Save hypotheses
    HypothesisAgent-->>Supervisor: Hypotheses ready
    
    Supervisor->>Approval: Request approval for exploit
    Approval->>User: Prompt approval
    User-->>Approval: Approve
    Approval-->>Supervisor: Approved
    
    Supervisor->>ExploitAgent: Test exploit
    ExploitAgent->>Storage: Save exploit
    ExploitAgent-->>Supervisor: Exploit verified
    
    Supervisor->>TriageAgent: Validate findings
    TriageAgent->>Storage: Update findings
    TriageAgent-->>Supervisor: Findings triaged
    
    Supervisor->>ReportingAgent: Generate report
    ReportingAgent->>Storage: Save report
    ReportingAgent-->>Supervisor: Report ready
    
    Supervisor-->>Workflow: Complete
    Workflow-->>CLI: Success
    CLI-->>User: Display results
```

## Module Size Distribution

```mermaid
pie title Lines of Code by Module
    "Agents" : 11604
    "Tools" : 3696
    "Core" : 3192
    "Workflows" : 1854
    "CLI" : 1060
    "Insights" : 925
    "Utils" : 660
    "Models" : 637
    "Root" : 215
    "Config" : 59
    "Fixtures" : 21
```

## Async vs Sync Functions

```mermaid
pie title Function Types Across Codebase
    "Async Functions" : 238
    "Sync Functions" : 193
```

## File Size Distribution

```mermaid
graph LR
    subgraph Large Files >400 LOC
        A1[Agents: 527 avg]
        A2[CLI: 353 avg]
    end
    
    subgraph Medium Files 200-400 LOC
        M1[Tools: 308 avg]
        M2[Workflows: 231 avg]
        M3[Insights: 231 avg]
        M4[Core: 212 avg]
    end
    
    subgraph Small Files <200 LOC
        S1[Models: 159 avg]
        S2[Utils: 110 avg]
        S3[Root: 107 avg]
        S4[Config: 29 avg]
        S5[Fixtures: 10 avg]
    end
    
    style A1 fill:#ff9999
    style A2 fill:#ff9999
    style M1 fill:#ffcc99
    style M2 fill:#ffcc99
    style M3 fill:#ffcc99
    style M4 fill:#ffcc99
    style S1 fill:#99ff99
    style S2 fill:#99ff99
    style S3 fill:#99ff99
    style S4 fill:#99ff99
    style S5 fill:#99ff99
```

## Agent Specialization Tree

```mermaid
graph TD
    BASE[Base Agent<br/>Abstract Class]
    
    BASE --> SUPER[Supervisor Agent<br/>Orchestration]
    BASE --> INFO[Information Gathering]
    BASE --> ANALYSIS[Analysis]
    BASE --> EXPLOIT[Exploitation]
    BASE --> REPORTING[Reporting]
    
    INFO --> RECON[Recon Agent]
    INFO --> INGEST[Program Ingest]
    INFO --> IMMUNEFI[Immunefi Intelligence]
    
    ANALYSIS --> HYPOTHESIS[Vuln Hypothesis]
    ANALYSIS --> STATIC[Static Analysis]
    ANALYSIS --> RESEARCH[Research Orchestrator]
    ANALYSIS --> ADVANCED[Advanced Research]
    ANALYSIS --> META[Meta Learning]
    
    EXPLOIT --> EXP[Exploit Agent]
    EXPLOIT --> SPEC[Exploit Specialists]
    EXPLOIT --> ORACLE[Oracle Detector]
    EXPLOIT --> VERIFY[Verifiers]
    
    REPORTING --> TRIAGE[Triage Agent]
    REPORTING --> REP[Reporting Agent]
    REPORTING --> PLAN[Planner Agent]
    
    style BASE fill:#cc99ff
    style SUPER fill:#ff9999
    style INFO fill:#99ccff
    style ANALYSIS fill:#ffcc99
    style EXPLOIT fill:#ff9999
    style REPORTING fill:#99ff99
```

## Tool Integration Map

```mermaid
graph TD
    TOOLS[Tools Module]
    
    subgraph External Services
        PERP[Perplexity<br/>Research API]
        IMF[Immunefi<br/>Bounty Platform]
        BROWSER[Browser<br/>Playwright]
    end
    
    subgraph External Binaries
        FOUNDRY[Foundry<br/>Smart Contract Testing]
        HARDHAT[Hardhat<br/>Development Env]
        SUBFINDER[Subfinder<br/>Subdomain Enum]
        AMASS[Amass<br/>Asset Discovery]
        HTTPX[HTTPX<br/>HTTP Probing]
    end
    
    subgraph Internal Services
        STORAGE[(SQLite<br/>Storage)]
        HTTP[HTTP Client<br/>httpx]
        OOB[Out-of-Band<br/>Testing]
    end
    
    TOOLS --> PERP
    TOOLS --> IMF
    TOOLS --> BROWSER
    TOOLS --> FOUNDRY
    TOOLS --> HARDHAT
    TOOLS --> SUBFINDER
    TOOLS --> AMASS
    TOOLS --> HTTPX
    TOOLS --> STORAGE
    TOOLS --> HTTP
    TOOLS --> OOB
    
    style TOOLS fill:#f3e1ff
    style External Services fill:#e1f5ff
    style External Binaries fill:#ffe1e1
    style Internal Services fill:#e1ffe1
```

## Security Control Flow

```mermaid
flowchart TD
    START[Action Request]
    
    START --> ACL{ACL Check}
    ACL -->|Denied| BLOCK[Block Action]
    ACL -->|Allowed| RATE{Rate Limit Check}
    
    RATE -->|Exceeded| BLOCK
    RATE -->|OK| SCOPE{Scope Check}
    
    SCOPE -->|Out of Scope| BLOCK
    SCOPE -->|In Scope| KILL{Kill Switch Active?}
    
    KILL -->|Yes| BLOCK
    KILL -->|No| RISK{High Risk Action?}
    
    RISK -->|Yes| APPROVAL{Human Approval}
    RISK -->|No| EXECUTE[Execute Action]
    
    APPROVAL -->|Denied| BLOCK
    APPROVAL -->|Approved| EXECUTE
    
    EXECUTE --> LOG[Log to Audit Trail]
    LOG --> DONE[Action Complete]
    
    BLOCK --> LOG_BLOCK[Log Blocked Action]
    LOG_BLOCK --> DONE
    
    style START fill:#e1f5ff
    style BLOCK fill:#ff9999
    style EXECUTE fill:#99ff99
    style APPROVAL fill:#ffcc99
    style DONE fill:#99ff99
```

## Workspace Structure

```
workspace/
├── 📁 recon/
│   ├── domains.txt                # Discovered domains
│   ├── targets.json               # Target endpoints
│   ├── subdomains.txt            # Subdomain enumeration
│   └── services.json             # Service fingerprints
│
├── 📁 hypotheses/
│   ├── hypotheses.json           # Vulnerability hypotheses
│   ├── enhanced/                 # Enhanced hypotheses
│   └── research/                 # Research context
│
├── 📁 exploits/
│   ├── exploit_001.sol           # Solidity exploits
│   ├── exploit_002.py            # Python exploits
│   ├── results/                  # Test results
│   └── artifacts/                # Build artifacts
│
├── 📁 findings/
│   ├── findings.json             # Validated findings
│   ├── verified/                 # Verified exploits
│   └── false_positives/          # FP analysis
│
├── 📁 logs/
│   ├── audit.jsonl               # Audit trail
│   ├── debug.log                 # Debug logs
│   ├── errors.log                # Error logs
│   └── performance.jsonl         # Performance metrics
│
├── 📁 reports/
│   ├── final_report.md           # Final report
│   ├── executive_summary.pdf     # Executive summary
│   └── insights_dashboard.html   # Insights dashboard
│
├── 📁 phases/
│   ├── recon.json                # Recon phase state
│   ├── hypothesis.json           # Hypothesis phase state
│   ├── exploit.json              # Exploit phase state
│   └── triage.json               # Triage phase state
│
└── 📁 learnings/
    ├── patterns.json             # Learned patterns
    ├── metrics.json              # Success metrics
    └── feedback.json             # User feedback
```

## Technology Stack

```mermaid
graph TB
    subgraph Runtime
        PYTHON[Python 3.10+]
        ASYNCIO[asyncio]
    end
    
    subgraph Core Libraries
        PYDANTIC[Pydantic<br/>Validation]
        STRUCTLOG[structlog<br/>Logging]
        HTTPX[httpx<br/>HTTP Client]
    end
    
    subgraph AI/ML
        GEMINI[Google Gemini<br/>Advisor]
        PERPLEXITY[Perplexity<br/>Research]
        TOGETHER[Together AI<br/>Workers]
    end
    
    subgraph Security Tools
        FOUNDRY_TECH[Foundry<br/>Smart Contracts]
        SLITHER[Slither<br/>Static Analysis]
        ECHIDNA[Echidna<br/>Fuzzing]
    end
    
    subgraph Data
        SQLITE[SQLite<br/>Metrics]
        JSONL[JSONL<br/>Logs]
        YAML_TECH[YAML<br/>Config]
    end
    
    PYTHON --> ASYNCIO
    PYTHON --> PYDANTIC
    PYTHON --> STRUCTLOG
    PYTHON --> HTTPX
    PYTHON --> SQLITE
    
    HTTPX --> GEMINI
    HTTPX --> PERPLEXITY
    HTTPX --> TOGETHER
    
    style PYTHON fill:#3776ab,color:#fff
    style ASYNCIO fill:#00d4aa
    style PYDANTIC fill:#e92063,color:#fff
    style GEMINI fill:#4285f4,color:#fff
    style FOUNDRY_TECH fill:#ff5733
```

---

*These visual representations complement the detailed [CODEMAP_ANALYSIS.md](../CODEMAP_ANALYSIS.md) document.*
