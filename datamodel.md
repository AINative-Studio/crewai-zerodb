Below is the **finalized ZeroDB-aligned data model** revised with the **exact namespace map** and the **filter recipes** you’ll implement in `ZeroDBKnowledgeTool`, `ZeroDBMemoryStore`, and `ZeroDBTracer`.

This stays strictly within ZeroDB primitives:

* **Projects**
* **Vectors** (namespace + metadata + filter)
* **Memory** (content/title/tags/priority/metadata + list/search/related)

---

# 1) Exact Namespace Map

## 1.1 Namespace Registry (authoritative)

Use this as a constant in the integration package.

```python
ZERODB_NAMESPACE_MAP = {
  # Static / curated knowledge (pre-ingested)
  "PLAYBOOKS":        "sales_playbooks",
  "CASE_STUDIES":     "sales_cases",

  # Dynamic knowledge (created by agents/humans over time)
  "ACCOUNTS":         "accounts",
  "LEADS":            "leads",
  "OUTREACH_HISTORY": "outreach_history",

  # Observability + replay artifacts
  "RUN_ARTIFACTS":    "crew_runs"
}
```

## 1.2 What goes where (single source of truth rules)

### `sales_playbooks`

* **What:** positioning, objection handling, email frameworks, persona playbooks
* **Write policy:** pre-ingest only (v1), optional on-the-fly in v1.1

### `sales_cases`

* **What:** case studies, win stories, ROI narratives
* **Write policy:** pre-ingest only (v1)

### `accounts`

* **What:** account research summaries, firmographics, buying signals, competitive landscape notes
* **Write policy:** agents write

### `leads`

* **What:** lead-specific notes that benefit from semantic recall (persona signals, objections, preferences)
* **Write policy:** agents + humans write (and optionally mirror some items from Memory)

### `outreach_history`

* **What:** outreach drafts/sent messages/replies/call notes
* **Write policy:** agents write

### `crew_runs`

* **What:** run summary, task summaries, tool-call summaries, structured traces (vectorized)
* **Write policy:** tracer writes automatically

---

# 2) Metadata Schemas (final, consistent keys)

## 2.1 Shared metadata keys (ALL vector records)

Every vector upsert metadata **must include**:

```json
{
  "type": "string",
  "ts": "ISO-8601 timestamp",
  "tags": ["key:value", "key:value"]
}
```

## 2.2 Sales-scoped keys (required when relevant)

```json
{
  "account_id": "acct_...",
  "lead_id": "lead_..."
}
```

## 2.3 CrewAI-scoped keys (required for run artifacts / traces)

```json
{
  "crew_id": "crew_sales_v1",
  "agent_id": "research_agent",
  "run_id": "run_...",
  "task_id": "task_..."
}
```

## 2.4 Type-specific metadata (by namespace)

### `sales_playbooks` / `sales_cases`

```json
{
  "doc_id": "doc_...",
  "title": "string",
  "source": "internal|url|file",
  "url": "https://...",
  "section": "string",
  "chunk_index": 0
}
```

### `accounts`

```json
{
  "type": "account_note",
  "account_id": "acct_...",
  "title": "Account Research Summary",
  "source": "agent|human|import",
  "stage": "research|outreach|followup",
  "run_id": "run_...",
  "task_id": "task_..."
}
```

### `leads`

```json
{
  "type": "lead_note",
  "lead_id": "lead_...",
  "account_id": "acct_...",
  "source": "agent|human|import",
  "stage": "research|outreach|followup",
  "run_id": "run_...",
  "task_id": "task_..."
}
```

### `outreach_history`

```json
{
  "type": "outreach",
  "artifact_id": "out_...",
  "account_id": "acct_...",
  "lead_id": "lead_...",
  "channel": "email|linkedin|sms|call|other",
  "variant": "v1|v2|subject_lines|...",
  "status": "draft|sent|reply_received|no_reply",
  "run_id": "run_...",
  "task_id": "task_..."
}
```

### `crew_runs`

```json
{
  "type": "trace",
  "trace_type": "run_summary|task_summary|tool_call",
  "crew_id": "crew_sales_v1",
  "agent_id": "string",
  "run_id": "run_...",
  "task_id": "task_...",
  "tool_call_id": "tool_...",
  "account_id": "acct_...",
  "lead_id": "lead_...",
  "stage": "research|outreach|followup",
  "ok": true,
  "duration_ms": 1234
}
```

---

# 3) Filter Recipes (Vectors)

ZeroDB vectors filtering works by passing a `filter` dict into `vectors.search(...)`. Your integration should generate these filters *deterministically* from the sales context + stage.

## 3.1 Global filter builder (canonical)

**Inputs:** `account_id?`, `lead_id?`, `stage?`, `types?`, `tags?`, `run_id?`

**Output filter dict:**

```json
{
  "account_id": "acct_...",
  "lead_id": "lead_...",
  "stage": "outreach",
  "type": "outreach",
  "run_id": "run_..."
}
```

### Rules

* Include `account_id` whenever you have it (most sales workflows do)
* Include `lead_id` when lead-specific retrieval is desired
* Include `stage` when you want stage-local relevance (often yes)
* Include `type` when searching across mixed types in the same namespace (always recommended)
* Include `run_id` only for run-scoped retrieval (replay/debug)

> If your ZeroDB filter supports tag membership, you can also filter by `tags`, but the safest/most portable approach is filtering on explicit scalar fields (`type`, `account_id`, etc.) and using tags for Memory + in-app ranking.

---

## 3.2 Namespace-specific filter recipes

### A) Playbooks (persona/vertical targeting)

**Namespace:** `sales_playbooks`
**When:** research/outreach/followup

**Filter recipe:**

```json
{
  "type": "playbook"
}
```

**Optional narrowing (preferred via tags, but can be scalar if you store it):**

* If you store `persona` and `vertical` as scalar fields:

```json
{ "type": "playbook", "persona": "cto", "vertical": "data_center" }
```

---

### B) Case studies (vertical + persona + account similarity)

**Namespace:** `sales_cases`

**Filter recipe:**

```json
{
  "type": "case_study"
}
```

**Optional narrowing:**

```json
{ "type": "case_study", "vertical": "data_center" }
```

---

### C) Account notes (account-scoped)

**Namespace:** `accounts`

**Filter recipe:**

```json
{
  "type": "account_note",
  "account_id": "acct_123"
}
```

**Stage narrowing (if you want just research notes):**

```json
{
  "type": "account_note",
  "account_id": "acct_123",
  "stage": "research"
}
```

---

### D) Lead notes (lead-scoped)

**Namespace:** `leads`

**Filter recipe:**

```json
{
  "type": "lead_note",
  "lead_id": "lead_456"
}
```

**Account+lead (recommended if lead_id might collide across sources):**

```json
{
  "type": "lead_note",
  "account_id": "acct_123",
  "lead_id": "lead_456"
}
```

---

### E) Outreach history (lead + channel + status)

**Namespace:** `outreach_history`

**Filter recipe (lead-scoped):**

```json
{
  "type": "outreach",
  "account_id": "acct_123",
  "lead_id": "lead_456"
}
```

**Filter recipe (channel-specific):**

```json
{
  "type": "outreach",
  "account_id": "acct_123",
  "lead_id": "lead_456",
  "channel": "email"
}
```

**Filter recipe (only sent + replies):**

```json
{
  "type": "outreach",
  "account_id": "acct_123",
  "lead_id": "lead_456",
  "status": "sent"
}
```

---

### F) Run artifacts + traces (replay/debug)

**Namespace:** `crew_runs`

**Filter recipe (entire run):**

```json
{
  "type": "trace",
  "run_id": "run_abc"
}
```

**Task-only:**

```json
{
  "type": "trace",
  "run_id": "run_abc",
  "trace_type": "task_summary",
  "task_id": "task_789"
}
```

**Tool-calls only (by tool name via tags or scalar field if stored):**

```json
{
  "type": "trace",
  "run_id": "run_abc",
  "trace_type": "tool_call"
}
```

---

# 4) Retrieval Recipes (exact “calls” the integration will make)

## 4.1 Knowledge retrieval for each stage (RAG)

### Research stage (best mix)

Search **3 namespaces** and merge results with simple scoring:

1. `sales_playbooks` (broad)
2. `sales_cases` (vertical-based)
3. `accounts` (account-specific)

**Filters**

* Playbooks: `{ "type": "playbook" }`
* Cases: `{ "type": "case_study", "vertical": <if available> }`
* Accounts: `{ "type": "account_note", "account_id": <account_id> }`

### Outreach stage (most personal)

Search **4 namespaces**:

1. `outreach_history` (lead-specific)
2. `leads` (lead notes)
3. `sales_playbooks` (persona playbooks)
4. `sales_cases` (1–2 relevant stories)

**Filters**

* Outreach: `{ "type": "outreach", "account_id": X, "lead_id": Y }`
* Leads: `{ "type": "lead_note", "account_id": X, "lead_id": Y }`

### Follow-up stage (objection handling)

Search:

1. `outreach_history`
2. `leads`
3. `sales_playbooks` (objection section)
4. `crew_runs` (prior run/task summaries for continuity)

**Filters**

* Run artifacts: `{ "type": "trace", "account_id": X, "lead_id": Y }`

  * (Optionally include `run_id` if you’re continuing the same run)

---

# 5) Memory Filter Recipes (Memory)

Memory has **two different retrieval modes** in the SDK:

## 5.1 Fast facet recall (authoritative)

Use `memory.list(tags=[...], priority=...)` for deterministic slices.

### Canonical memory tags (exact)

Always include:

* `account:acct_123`
* `lead:lead_456` (if lead-scoped)
* `stage:research|outreach|followup`
* `type:preference|objection|decision|next_step|summary`
* `entity:account|entity:lead|entity:run`

### Recipes

**Lead preferences (always pull before outreach):**

* tags:

  * `entity:lead`
  * `account:acct_123`
  * `lead:lead_456`
  * `type:preference`
* priority: `HIGH`

**Open objections (before follow-up):**

* tags:

  * `entity:lead`
  * `lead:lead_456`
  * `type:objection`
* priority: `MEDIUM+`

**Next steps (always pull at start of follow-up):**

* tags:

  * `entity:lead`
  * `lead:lead_456`
  * `type:next_step`
* priority: `HIGH`

## 5.2 Semantic recall (best-effort)

Use `memory.search(query=..., semantic=True, limit=N)` and **post-filter in app code** by:

* `metadata.account_id == account_id`
* `metadata.lead_id == lead_id`

### Post-filter recipe (exact)

After `memory.search(...)`, keep items where:

* If `lead_id` present: match both `account_id` and `lead_id`
* Else: match `account_id`

This gives you “meaning-based” recall without inventing unsupported server-side filters.

---

# 6) “Exact” Filter-Generation Cheatsheet (what your code should do)

Given `context = {account_id, lead_id, stage, run_id, crew_id}`:

## KnowledgeTool.search() default plan (Sales Crew)

1. Build `queries = [user_query]`
2. Execute searches in this exact order:

### Research stage

* `sales_playbooks` filter `{type:"playbook"}`
* `sales_cases` filter `{type:"case_study", vertical: <if known>}`
* `accounts` filter `{type:"account_note", account_id}`

### Outreach stage

* `outreach_history` filter `{type:"outreach", account_id, lead_id}`
* `leads` filter `{type:"lead_note", account_id, lead_id}`
* `sales_playbooks` filter `{type:"playbook"}` (+ optional persona)
* `sales_cases` filter `{type:"case_study"}` (+ optional vertical)

### Follow-up stage

* `outreach_history` filter `{type:"outreach", account_id, lead_id}`
* `leads` filter `{type:"lead_note", account_id, lead_id}`
* `sales_playbooks` filter `{type:"playbook"}`
* `crew_runs` filter `{type:"trace", account_id, lead_id}` (or `{run_id}` if same run)

3. Merge results, de-dup by `(namespace, doc_id/chunk_index or artifact_id)`
4. Return top `N` with citations.

---
