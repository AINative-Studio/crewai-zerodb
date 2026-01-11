# BACKLOG — ZeroDB Integration for CrewAI (OSS)

**Product:** `crewai-zerodb`
**Anchor Use Case:** Sales Agent Crew (Research → Outreach → Follow-up)
**Architecture:** ZeroDB (Projects, Vectors, Memory) via AINative Python SDK
**Non-Goals:** No UI, no CrewAI Cloud, no raw chat persistence by default

---

## EPIC 0 — Project Foundation & OSS Readiness

**Goal:** Ensure the repo is installable, testable, documented, and hackathon-ready.

### Story 0.1 — Initialize OSS repository

**As a** maintainer
**I want** a clean Python package scaffold
**So that** contributors can install and run it immediately

**Acceptance Criteria**

* `crewai_zerodb/` package exists
* `pyproject.toml` or `setup.py` configured
* Python >= 3.10 supported
* License file (MIT or Apache 2.0)

**Estimate:** 1

---

### Story 0.2 — Add dependency wiring for AINative SDK

**As a** developer
**I want** the integration to rely exclusively on the official Python SDK
**So that** we stay 100% ZeroDB-aligned

**Acceptance Criteria**

* `ainative` SDK added as dependency
* No custom HTTP clients
* All ZeroDB access via SDK calls only

**Estimate:** 1

---

### Story 0.3 — Add project configuration loader

**As a** developer
**I want** a single config surface for API keys and project scoping
**So that** setup is predictable

**Acceptance Criteria**

* Reads `AINATIVE_API_KEY`
* Reads optional `AINATIVE_ORG_ID`
* Reads or auto-creates `ZERODB_PROJECT_ID`
* Config errors fail fast

**Estimate:** 2

---

## EPIC 1 — ZeroDB Namespace & Schema Enforcement

**Goal:** Encode the **exact namespace map and metadata rules** so nothing drifts.

### Story 1.1 — Implement namespace registry

**As a** developer
**I want** a canonical namespace map
**So that** all tools use consistent ZeroDB collections

**Acceptance Criteria**

* Namespace enum exists
* Matches finalized spec exactly:

  * `sales_playbooks`
  * `sales_cases`
  * `accounts`
  * `leads`
  * `outreach_history`
  * `crew_runs`

**Estimate:** 1

---

### Story 1.2 — Enforce shared metadata schema

**As a** developer
**I want** all vector metadata to pass schema validation
**So that** filters always work

**Acceptance Criteria**

* `type`, `ts`, `tags[]` required
* Tag format enforced (`key:value`)
* Validation fails on invalid metadata

**Estimate:** 2

---

### Story 1.3 — Enforce sales-scoped metadata rules

**As a** developer
**I want** account/lead requirements enforced per namespace
**So that** bad data cannot be written

**Acceptance Criteria**

* `accounts` requires `account_id`
* `leads` requires `account_id + lead_id`
* `outreach_history` requires both
* `crew_runs` requires `crew_id + run_id`

**Estimate:** 2

---

## EPIC 2 — ZeroDB Knowledge Tool (RAG)

**Goal:** Provide deterministic, stage-aware RAG across namespaces.

### Story 2.1 — Implement KnowledgeTool interface

**As a** CrewAI developer
**I want** a `ZeroDBKnowledgeTool`
**So that** agents can retrieve knowledge without boilerplate

**Acceptance Criteria**

* Tool accepts query + sales context
* Uses SDK `vectors.search`
* Returns snippets + metadata + namespace

**Estimate:** 2

---

### Story 2.2 — Implement research-stage search plan

**As a** sales agent
**I want** research to pull from playbooks, cases, and account notes
**So that** context is comprehensive

**Acceptance Criteria**

* Searches namespaces in order:

  1. `sales_playbooks`
  2. `sales_cases`
  3. `accounts`
* Uses exact filter recipes
* Results merged + deduped

**Estimate:** 3

---

### Story 2.3 — Implement outreach-stage search plan

**As a** sales agent
**I want** outreach to prioritize lead-specific context
**So that** messages are personalized

**Acceptance Criteria**

* Searches namespaces:

  1. `outreach_history`
  2. `leads`
  3. `sales_playbooks`
  4. `sales_cases`
* Lead + account filters enforced

**Estimate:** 3

---

### Story 2.4 — Implement follow-up search plan

**As a** follow-up agent
**I want** objections and past outreach retrieved automatically
**So that** follow-ups are intelligent

**Acceptance Criteria**

* Searches namespaces:

  * `outreach_history`
  * `leads`
  * `sales_playbooks`
  * `crew_runs`
* Supports run-scoped replay

**Estimate:** 3

---

## EPIC 3 — ZeroDB Memory Store (Durable Agent Memory)

**Goal:** Persist **high-signal sales memory**, not noise.

### Story 3.1 — Implement MemoryStore abstraction

**As a** developer
**I want** a MemoryStore wrapper
**So that** memory writes are consistent

**Acceptance Criteria**

* Wraps `zerodb.memory.create`
* Accepts content, tags, priority, metadata
* Rejects missing required tags

**Estimate:** 2

---

### Story 3.2 — Implement memory tag builders

**As a** developer
**I want** canonical memory tags
**So that** memory.list() is deterministic

**Acceptance Criteria**

* Tags include:

  * `entity:*`
  * `type:*`
  * `stage:*`
* Optional: `account:*`, `lead:*`, `channel:*`

**Estimate:** 2

---

### Story 3.3 — Implement facet-based memory recall

**As a** sales agent
**I want** fast retrieval of preferences, objections, next steps
**So that** I don’t rely on fuzzy search

**Acceptance Criteria**

* Uses `memory.list(tags=...)`
* Supports:

  * lead preferences
  * objections
  * next steps
* Priority respected

**Estimate:** 3

---

### Story 3.4 — Implement semantic memory recall

**As a** sales agent
**I want** meaning-based memory search
**So that** I can recall context even if phrasing changes

**Acceptance Criteria**

* Uses `memory.search(semantic=True)`
* Post-filters by account_id / lead_id
* Results ranked by relevance

**Estimate:** 3

---

## EPIC 4 — ZeroDB Tracer (Observability & Replay)

**Goal:** Make CrewAI runs **inspectable and replayable**.

### Story 4.1 — Implement Run lifecycle tracing

**As a** developer
**I want** run start/end captured automatically
**So that** every execution is traceable

**Acceptance Criteria**

* Run start event written
* Run summary written to `crew_runs`
* Includes crew_id, run_id, ts

**Estimate:** 2

---

### Story 4.2 — Implement Task lifecycle tracing

**As a** developer
**I want** task start/end summaries
**So that** agent behavior is debuggable

**Acceptance Criteria**

* Task summaries vectorized
* Includes task_id, agent_id, stage
* Stored in `crew_runs`

**Estimate:** 3

---

### Story 4.3 — Implement Tool call tracing

**As a** developer
**I want** tool calls traced without noise
**So that** failures are visible

**Acceptance Criteria**

* Tool name + duration logged
* Errors captured
* Inputs/outputs summarized (not raw)

**Estimate:** 3

---

## EPIC 5 — Sales Crew Demo (End-to-End Validation)

**Goal:** Prove the system works in a real sales workflow.

### Story 5.1 — Implement ResearchAgent demo

**As a** demo user
**I want** a research agent using RAG + memory
**So that** account context persists

**Acceptance Criteria**

* Research summary stored
* Account notes vectorized
* Memory written

**Estimate:** 2

---

### Story 5.2 — Implement OutreachAgent demo

**As a** demo user
**I want** outreach drafts stored and recalled
**So that** follow-ups adapt

**Acceptance Criteria**

* Draft stored in `outreach_history`
* Decision memory written
* Lead preferences respected

**Estimate:** 3

---

### Story 5.3 — Implement FollowUpAgent demo

**As a** demo user
**I want** objections + next steps recalled
**So that** the agent behaves intelligently

**Acceptance Criteria**

* Objections recalled from memory
* Follow-up plan stored
* Next steps persisted

**Estimate:** 3

---

## EPIC 6 — Quality, Tests & Documentation

**Goal:** Make the project safe to adopt and contribute to.

### Story 6.1 — Unit tests for filter builders

**As a** maintainer
**I want** filter logic tested
**So that** retrieval never breaks

**Acceptance Criteria**

* Tests for each namespace filter recipe
* Edge cases covered

**Estimate:** 2

---

### Story 6.2 — Unit tests for Pydantic models

**As a** maintainer
**I want** schema enforcement tested
**So that** invalid data is rejected

**Estimate:** 2

---

### Story 6.3 — Write README with Sales Crew walkthrough

**As a** new user
**I want** a step-by-step guide
**So that** I can run the demo in minutes

**Acceptance Criteria**

* Install instructions
* Minimal code example
* Sales demo explanation

**Estimate:** 3

---

