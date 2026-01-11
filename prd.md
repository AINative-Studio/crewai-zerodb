# Product Requirements Document (PRD)

## ZeroDB Integration for CrewAI (Open Source)

**Product Name:** `crewai-zerodb`
**Version:** v1.0 (OSS)
**Owner:** AINative Studio
**Target Users:**

* Developers building CrewAI agents
* Founders & growth teams building AI sales agents
* Hackathon teams & OSS contributors

**Non-Goals (Explicit):**

* No CrewAI Cloud integration
* No UI / dashboard in v1
* No proprietary CrewAI forks
* No raw chat persistence by default

---

## 1. Executive Summary

This project delivers a **first-class, open-source integration between CrewAI and ZeroDB**, enabling **persistent memory, RAG, and observability** for agent crews—starting with a **Sales Agent Crew** workflow.

The integration is designed to:

* Be **drop-in simple** (minimal wiring)
* Follow **OSS best practices**
* Use **ZeroDB as durable agent state**, not just vector storage
* Showcase ZeroDB’s strengths in **memory, replay, and multi-agent handoff**

The result is a CrewAI experience where agents **remember past deals, reuse knowledge, and become debuggable and replayable**—without requiring users to build their own storage layer.

---

## 2. Problem Statement

CrewAI provides powerful multi-agent orchestration, but in OSS usage today:

1. **Memory is ephemeral**

   * Agent context disappears between runs
   * No durable “account memory” or “lead preferences”

2. **RAG is ad-hoc**

   * Users must manually wire vector stores
   * No shared or evolving knowledge base across runs

3. **Observability is weak**

   * Hard to debug agent behavior
   * No standardized run/task/tool traces
   * No replay or evaluation workflow

4. **Sales workflows suffer**

   * Sales agents must remember:

     * account context
     * objections
     * outreach history
     * next steps
   * Without persistence, agents repeat themselves or regress

---

## 3. Goals & Success Criteria

### Primary Goals

* Enable **persistent memory** across CrewAI runs
* Enable **ZeroDB-backed RAG** with minimal setup
* Provide **run/task/tool observability** without user boilerplate
* Make ZeroDB feel **native** to CrewAI

### Success Criteria

* A developer can add ZeroDB to a CrewAI project in **<15 lines**
* A sales crew can:

  * remember a lead across runs
  * retrieve past outreach
  * adapt follow-ups based on memory
* The integration is:

  * pip-installable
  * documented
  * demo-ready for hackathons

---

## 4. Target Use Case (Anchor)

### Sales Agent Crew Workflow

**Stages:**

1. Research
2. Outreach
3. Follow-Up

**Key Requirements:**

* Remember account & lead context
* Retrieve playbooks and similar past deals
* Store outreach artifacts
* Persist decisions and next steps
* Allow replay/debug of a run

---

## 5. Architecture Overview

### High-Level Components

```
CrewAI
 ├─ Agents
 ├─ Tasks
 ├─ Tools
 └─ Callbacks
        ↓
ZeroDB Integration Layer
 ├─ Knowledge Tool (RAG)
 ├─ Memory Store
 └─ Tracer (Observability)
        ↓
AINative Python SDK
        ↓
ZeroDB Backend
```

**Key Constraint:**
All ZeroDB interaction **must use the existing AINative Python SDK**.

---

## 6. Functional Requirements

### 6.1 ZeroDB Knowledge Tool (RAG)

**Purpose:**
Provide semantic retrieval over sales knowledge.

**Supported Knowledge Types:**

* Sales playbooks
* Case studies
* Past account notes
* Outreach history
* Run artifacts (summaries, decisions)

**Requirements:**

* Namespace-scoped vector search
* Metadata filtering
* Citation-friendly results
* Read-only by default (write optional)

**Example Namespaces:**

* `sales_playbooks`
* `sales_cases`
* `accounts`
* `leads`
* `outreach_history`
* `crew_runs`

**Acceptance Criteria:**

* Agent can retrieve relevant context in a task
* Returned results include text + metadata
* Search supports filters (account_id, lead_id, tags)

---

### 6.2 ZeroDB Memory Store

**Purpose:**
Persist **curated memory**, not raw chat logs.

**Memory Types:**

1. **Episodic Memory**

   * Run summaries
   * Task outcomes
   * Key decisions

2. **Semantic Memory**

   * Lead preferences
   * Account pain points
   * Objections
   * Budget/timeline info
   * Next steps

**Default Persistence Policy (Opinionated):**

* ✅ Store summaries & extracted facts
* ❌ Do not store raw chat
* ❌ Do not store full tool IO (summary only)

**Required Operations:**

* Write memory with tags + metadata
* Recall memory by:

  * lead_id
  * account_id
  * semantic query
* Optional embedding for semantic recall

**Acceptance Criteria:**

* Follow-up agent can recall prior outreach context
* Memory persists across independent runs
* Memory is queryable by both ID and meaning

---

### 6.3 ZeroDB Tracer (Observability)

**Purpose:**
Make CrewAI runs **inspectable, debuggable, and replayable**.

**Captured Events:**

* Run start / end
* Task start / end
* Tool calls:

  * tool name
  * duration
  * error (if any)
  * input/output summary

**Stored As:**

* Structured events (metadata)
* Run summaries (memory)
* Artifacts (vectors, namespace `crew_runs`)

**Replay Support (v1 scope):**

* Store sufficient context to:

  * inspect what happened
  * manually re-run with same inputs

**Acceptance Criteria:**

* Developer can see:

  * which tools ran
  * which tasks succeeded/failed
* A run summary is persisted automatically

---

## 7. Sales Crew Functional Flow

### 7.1 Research Task

**Inputs:**

* lead_id
* account_id
* product context

**ZeroDB Interactions:**

* RAG search:

  * playbooks
  * similar accounts
* Write:

  * research summary (memory)
  * extracted facts (memory)
  * sources used (trace artifact)

---

### 7.2 Outreach Task

**Inputs:**

* research summary
* channel (email / LinkedIn)

**ZeroDB Interactions:**

* Recall:

  * lead preferences
  * past objections
* Write:

  * outreach draft (vector)
  * decision rationale (memory)

---

### 7.3 Follow-Up Task

**Inputs:**

* reply or no-reply signal

**ZeroDB Interactions:**

* Recall:

  * outreach history
  * objections
* Write:

  * follow-up plan
  * updated status
  * next steps (memory)

---

## 8. Data Model (Logical)

### Memory Entry

```
content: string
tags: [ "type:preference", "stage:outreach" ]
metadata:
  account_id
  lead_id
  run_id
  task_id
  source
```

### Vector Artifact

```
text: string
namespace: "outreach_history"
metadata:
  account_id
  lead_id
  run_id
  artifact_type
```

### Trace Event

```
event_type: run_start | task_end | tool_call
timestamp
run_id
task_id
agent_id
summary
```

---

## 9. Developer Experience (DX)

### Installation

```bash
pip install crewai-zerodb
```

### Minimal Usage

```python
from crewai_zerodb import (
  ZeroDBKnowledgeTool,
  ZeroDBMemoryStore,
  ZeroDBTracer
)
```

**DX Principles:**

* One-line instrumentation
* Sensible defaults
* Explicit opt-ins for heavy persistence

---

## 10. Configuration

### Environment Variables

* `AINATIVE_API_KEY` (required)
* `AINATIVE_ORG_ID` (optional)
* `ZERODB_PROJECT_ID` (optional)

### Config Flags

* `persist_raw_messages` (default: false)
* `persist_tool_io` (summary | full)
* `pii_redaction` (default: true)
* `retention_days` (optional)

---

## 11. Non-Functional Requirements

### Security

* No secrets stored in memory
* Optional PII redaction
* Project-scoped isolation

### Performance

* Batch vector writes
* Avoid per-token persistence
* Async-safe design

### OSS Requirements

* Apache or MIT license
* Clear README + examples
* No vendor lock-in beyond ZeroDB

---

## 12. Out of Scope (v1)

* UI dashboards
* Eval scoring & leaderboards
* Automatic CRM sync
* Cloud-hosted CrewAI support

---

## 13. Milestones

### Milestone 1 – Core Integration

* Knowledge Tool
* Memory Store
* Tracer
* Sales demo script

### Milestone 2 – Polish

* Docs & examples
* Tests
* Hackathon-ready walkthrough

---

## 14. Risks & Mitigations

| Risk                  | Mitigation             |
| --------------------- | ---------------------- |
| Over-persisting noise | Summary-first defaults |
| Complex setup         | Opinionated defaults   |
| Privacy concerns      | No raw chat by default |

---

## 15. Definition of Done

* Sales Crew demo works end-to-end
* Memory persists across runs
* RAG returns relevant results
* Traces visible in ZeroDB
* README enables <15-minute setup

---

## 16. Future Extensions (Post-v1)

* Eval hooks (win/loss labeling)
* Agent handoff memory
* CRM adapters
* Replay CLI
* Multi-crew shared memory

---

