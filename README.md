```markdown
# crewai-zerodb

**Persistent Memory, RAG, and Observability for CrewAI — powered by ZeroDB**

`crewai-zerodb` is an open-source integration that connects the **CrewAI Agent Framework (OSS)** with **ZeroDB** via the official **AINative Python SDK**.

It enables:
- 🧠 **Durable agent memory** (preferences, objections, next steps)
- 📚 **ZeroDB-backed RAG** across sales knowledge, cases, and history
- 🔍 **Run / task / tool observability** with replay-ready artifacts
- 🤝 **Multi-agent continuity** across independent runs

The integration is opinionated, minimal, and hackathon-ready.

---

## Why This Exists

CrewAI is excellent at orchestrating agents, but in OSS usage:

- Memory is ephemeral  
- RAG wiring is ad-hoc  
- Debugging agent behavior is difficult  

ZeroDB provides durable agent state — not just vectors.

This repo makes ZeroDB feel **native** to CrewAI.

---

## Features (v1)

### ✅ ZeroDB Knowledge Tool (RAG)
- Stage-aware retrieval (research / outreach / follow-up)
- Deterministic namespace + filter recipes
- Citation-friendly results

### ✅ ZeroDB Memory Store
- Curated long-term memory (not raw chat)
- Facet-based recall (preferences, objections, next steps)
- Semantic recall with post-filtering

### ✅ ZeroDB Tracer
- Run start / end
- Task summaries
- Tool-call summaries (no noisy raw logs)
- Replay-ready artifacts stored in ZeroDB

### ✅ Sales Crew Demo
- Research → Outreach → Follow-up
- Memory persists across runs
- Follow-ups adapt based on past context

---

## Non-Goals (Explicit)

- ❌ CrewAI Cloud
- ❌ UI / Dashboard
- ❌ Raw chat persistence by default
- ❌ CRM sync (future extension)

---

## Architecture Overview

```

CrewAI
├─ Agents
├─ Tasks
├─ Tools
└─ Callbacks
↓
crewai-zerodb
├─ KnowledgeTool (RAG)
├─ MemoryStore
└─ Tracer
↓
AINative Python SDK
↓
ZeroDB

````

---

## ZeroDB Namespace Map (Authoritative)

| Purpose | Namespace |
|------|-----------|
| Sales Playbooks | `sales_playbooks` |
| Case Studies | `sales_cases` |
| Account Notes | `accounts` |
| Lead Notes | `leads` |
| Outreach History | `outreach_history` |
| Runs & Traces | `crew_runs` |

---

## Installation

```bash
pip install crewai-zerodb
````

> Requires **Python 3.10+**

---

## Configuration

Create a `.env` file or export environment variables:

```bash
export AINATIVE_API_KEY=your_api_key_here
export AINATIVE_ORG_ID=optional_org_id
export ZERODB_PROJECT_ID=optional_existing_project
```

If `ZERODB_PROJECT_ID` is not provided, the integration will create or resolve one automatically.

---

## Minimal Usage Example

```python
from crewai_zerodb import (
    ZeroDBKnowledgeTool,
    ZeroDBMemoryStore,
    ZeroDBTracer,
)
```

These components are designed to be **plug-and-play** with CrewAI agents and callbacks.

---

## Sales Crew Demo (End-to-End)

### 1. Research Run

* Retrieves playbooks + cases + account notes
* Stores:

  * Research summary (memory)
  * Account notes (vectors)

### 2. Outreach Run

* Recalls lead preferences + past context
* Generates outreach drafts
* Stores:

  * Outreach artifacts
  * Decision rationale

### 3. Follow-Up Run

* Recalls objections + outreach history
* Adapts follow-up strategy
* Stores:

  * Next steps
  * Updated status

👉 **Second run references memory from the first run automatically**

---

## Example

```bash
python examples/sales_crew.py
```

Run it twice to see memory persistence in action.

---

## Memory Philosophy (Important)

This integration is **intentionally opinionated**:

* ✅ Store **facts, decisions, summaries**
* ❌ Do NOT store raw chat by default
* ❌ Do NOT store token-level logs

Memory is treated as **high-signal state**, not exhaust.

---

## Project Structure

```
crewai_zerodb/
├── config.py           # env + project resolution
├── models.py           # Pydantic schemas (metadata, filters, tags)
├── knowledge_tool.py   # ZeroDB RAG tool
├── memory_store.py     # Durable agent memory
├── tracer.py           # Run / task / tool observability
├── utils/
│   └── filters.py
examples/
├── sales_crew.py       # Research → Outreach → Follow-up demo
tests/
└── ...
```

---

## Testing

Lightweight but real:

* Unit tests for:

  * Filter builders
  * Pydantic schema validation
* Manual verification:

  * Run the sales demo twice
  * Confirm memory recall + traces in ZeroDB

---

## OSS & Contributions

* License: **MIT** (or Apache 2.0 if preferred)
* PRs welcome
* Please keep:

  * Stories ≤ size 3
  * Changes aligned with ZeroDB primitives
  * No custom clients (SDK only)

---

## Roadmap (Post-v1)

* Agent handoff memory
* Eval hooks (win/loss, task success)
* Replay helpers
* CRM adapters
* CLI runner

---

## Maintainers

Built by **AINative Studio**
Powered by **ZeroDB**

---

## TL;DR

If you’re building **serious CrewAI agents** and want them to:

* remember past work
* retrieve real knowledge
* be debuggable and replayable

👉 this repo is your missing persistence layer.

Happy building 🚀

```

---

```
