# ⚡ 8-Hour Agile Sprint Plan

**Product:** `crewai-zerodb`
**Sprint Type:** Single-day “Hardening MVP”
**Methodology:** XP-style, TDD-lean, vertical slices
**Definition of Done:** Sales Crew demo runs end-to-end with memory + RAG + tracing

---

## 🧭 Sprint Strategy (Read This First)

### What we WILL build

✅ Knowledge Tool (RAG)
✅ Memory Store (curated, tagged)
✅ Tracer (run/task/tool)
✅ Sales Crew demo (research → outreach → follow-up)
✅ README + example

### What we WILL NOT build

❌ UI
❌ CRM sync
❌ Full eval framework
❌ Raw chat persistence

---

## ⏱️ Hour-by-Hour Plan

---

## **Hour 0–0.5 — Sprint Setup & Lock Scope (30 min)**

**Goals**

* Lock sprint scope
* Prep environment
* Avoid mid-sprint derailment

**Tasks**

* Create repo (or branch)
* Install deps:

  * `ainative`
  * `crewai`
  * `pydantic`
* Add `.env.example`
* Copy in:

  * Namespace map
  * Pydantic models (already done)

**Exit Criteria**

* `pip install -e .` works
* Tests can run (even if empty)

---

## **Hour 0.5–1.5 — Core Infrastructure (60 min)**

### Vertical Slice: “Nothing breaks later”

**Tasks**

1. Implement `config.py`

   * Load API key
   * Resolve or create ZeroDB Project
2. Implement namespace registry
3. Wire SDK client creation

**Acceptance Criteria**

* Config object instantiates cleanly
* Project ID resolved deterministically
* No network calls outside SDK

**Artifacts**

* `config.py`
* `client.py`

---

## **Hour 1.5–3.0 — Knowledge Tool (RAG) (90 min)**

### Vertical Slice: “Agent can retrieve context”

**Tasks**

1. Implement `ZeroDBKnowledgeTool`
2. Implement filter builders
3. Implement **stage-aware search plans**
4. Merge + dedupe results

**Scope Control**

* Top-K fixed
* No reranking
* No hybrid search

**Acceptance Criteria**

* Research stage pulls:

  * playbooks
  * cases
  * account notes
* Outreach stage pulls lead + outreach history
* Follow-up stage pulls objections + traces

**Artifacts**

* `knowledge_tool.py`
* Unit tests for filter recipes

---

## **Hour 3.0–4.5 — Memory Store (90 min)**

### Vertical Slice: “Agent remembers things across runs”

**Tasks**

1. Implement `ZeroDBMemoryStore`
2. Implement memory tag builders
3. Implement:

   * `remember()`
   * `recall_by_facets()`
   * `recall_semantic()`

**Strict Rules**

* No raw chat
* Memory = high-signal facts only

**Acceptance Criteria**

* Can store:

  * preferences
  * objections
  * next steps
* Follow-up agent recalls prior run memory

**Artifacts**

* `memory_store.py`
* Memory tests

---

## **Hour 4.5–6.0 — Tracer (Observability) (90 min)**

### Vertical Slice: “I can debug what just happened”

**Tasks**

1. Implement `ZeroDBTracer`
2. Capture:

   * run start/end
   * task summaries
   * tool calls (summary only)
3. Write artifacts to `crew_runs`

**Minimalism Rule**

* One vector per event
* Summaries only
* No token-level logs

**Acceptance Criteria**

* Run artifacts visible in ZeroDB
* Can retrieve traces by run_id
* Tool failures are captured

**Artifacts**

* `tracer.py`
* Trace metadata schemas

---

## **Hour 6.0–7.0 — Sales Crew Demo (60 min)**

### Vertical Slice: “Judge-wow path”

**Tasks**

1. Build `examples/sales_crew.py`
2. Define agents:

   * ResearchAgent
   * OutreachAgent
   * FollowUpAgent
3. Wire:

   * KnowledgeTool
   * MemoryStore
   * Tracer

**Demo Script**

* Run #1: Research + Outreach
* Run #2: Follow-up (memory recalled)

**Acceptance Criteria**

* Second run references first run context
* Outreach adapts based on memory
* No crashes

---

## **Hour 7.0–8.0 — Hardening & Polish (60 min)**

### Vertical Slice: “Ship it”

**Tasks**

1. Write README:

   * Install
   * Env setup
   * Demo run
2. Add guardrails:

   * Better errors
   * Clear logs
3. Final pass:

   * Remove dead code
   * Format
   * Quick smoke test

**Acceptance Criteria**

* New user can run demo in <10 minutes
* Repo looks intentional
* No TODOs in core path

---

## 🧪 Testing Strategy (Light but Real)

* Unit tests:

  * Filter builders
  * Pydantic validation
* Manual test:

  * Sales demo twice in a row
* No full CI needed for sprint

---

## 📦 Final Deliverables (End of Hour 8)

✅ OSS-ready Python package
✅ ZeroDB-aligned data model
✅ Deterministic RAG + memory
✅ Observable CrewAI runs
✅ Sales demo that *actually remembers things*

---

## 🚀 If You Finish Early (Stretch, Optional)

* Add memory summarization at task end
* Add CLI runner
* Add “replay run” helper

---

